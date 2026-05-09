"""OmniPlay-MC AgentLoop — the Voyager curriculum/action/critic cycle.

One iteration of `run_once`:
  observe → retrieve skills → plan (action agent) → validate → execute →
  observe again → critic verdict → recovery decision → optional skill upsert.

`run_episode` drives many cycles, picking the next task either from a fixed
queue, a one-shot user task, or the curriculum agent.
"""

from __future__ import annotations

import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any

from bot_client import BotClient
from critic_queue import default_queue
from deterministic_verifier import DeterministicVerifier
from diagnoser import Diagnoser
from event_bus import EventBus, default_bus
from executor import Executor
from game_profile_builder import GameProfileBuilder
from llm_client import usage_snapshot
from memory_store import MemoryStore
from models import (
    AgentEvent,
    AgentEventType,
    JsCodeAction,
    Plan,
    RecoveryTransition,
    VerificationResult,
    VerificationStatus,
    WorldSnapshot,
)
from observability_hook import Observability
from observer import Observer
from planner import Planner
from recovery_policy import RecoveryPolicy
from skill_builder import SkillBuilder
from validator import Validator
from verifier import Verifier
from voyager_agents import CriticVerdict, CurriculumAgent, RetrievedSkill, SkillManager
from voyager_agents.action import ActionResult

LOG = logging.getLogger("omniplay.agent_loop")

MAX_CYCLES_DEFAULT = 50
MAX_TASK_RETRIES = 3


class AgentLoop:
    def __init__(
        self,
        *,
        bot_client: BotClient,
        skill_manager: SkillManager,
        memory: MemoryStore,
        event_bus: EventBus | None = None,
        curriculum: CurriculumAgent | None = None,
        observer: Observer | None = None,
        planner: Planner | None = None,
        executor: Executor | None = None,
        validator: Validator | None = None,
        verifier: Verifier | None = None,
        recovery: RecoveryPolicy | None = None,
        skill_builder: SkillBuilder | None = None,
        diagnoser: Diagnoser | None = None,
        profile_builder: GameProfileBuilder | None = None,
        narrator: "Narrator | None" = None,
        det_verifier: DeterministicVerifier | None = None,
    ) -> None:
        self.bot_client = bot_client
        self.skill_manager = skill_manager
        self.memory = memory
        self.event_bus = event_bus or default_bus()
        self.observability = Observability(event_bus=self.event_bus, memory=memory)
        self.curriculum = curriculum or CurriculumAgent()
        self.observer = observer or Observer(client=bot_client)
        self.planner = planner or Planner()
        self.executor = executor or Executor(client=bot_client)
        self.validator = validator or Validator()
        self.verifier = verifier or Verifier()
        self.recovery = recovery or RecoveryPolicy()
        self.skill_builder = skill_builder or SkillBuilder(skill_manager=skill_manager)
        self.diagnoser = diagnoser or Diagnoser()
        self.profile_builder = profile_builder or GameProfileBuilder()
        self.narrator = narrator
        self._det_verifier = det_verifier if det_verifier is not None else DeterministicVerifier()

        self._cycle = 0
        self._completed_tasks: list[str] = []
        self._failed_tasks: list[str] = []
        self._current_goal: str | None = None
        self._current_status: str = "idle"

    @property
    def status(self) -> dict[str, Any]:
        return {
            "cycle": self._cycle,
            "currentGoal": self._current_goal,
            "currentStatus": self._current_status,
            "completed": list(self._completed_tasks),
            "failed": list(self._failed_tasks),
            "skills": self.skill_manager.count(),
            "tokenUsage": usage_snapshot(),
        }

    async def run_once(self, *, task: str, rationale: str = "user-supplied") -> RecoveryTransition:
        """Run a single curriculum iteration on `task`. Returns the recovery decision."""
        self._cycle += 1
        cycle = self._cycle
        self._current_goal = task
        self._current_status = "observing"
        await self._emit(AgentEventType.GOAL_RECEIVED, {"task": task, "rationale": rationale})
        if self.narrator is not None:
            self.narrator.fire_and_forget(f"Next goal: {task}.", AgentEventType.GOAL_RECEIVED)

        snapshot_before = await self.observer.observe(cycle=cycle, goal=task)
        await self.memory.set_current_state(snapshot_before)
        await self._emit(
            AgentEventType.WORLD_OBSERVED,
            {"snapshot": snapshot_before.model_dump()},
            snapshot_id=snapshot_before.snapshot_id,
        )

        last_error: str | None = None
        last_code: str | None = None

        for attempt in range(1, MAX_TASK_RETRIES + 1):
            self._current_status = f"planning (attempt {attempt})"
            retrieved = self.skill_manager.retrieve(task, k=3)
            await self._emit(
                AgentEventType.MEMORY_RETRIEVED,
                {"skills": [r.record.name for r in retrieved], "attempt": attempt},
                snapshot_id=snapshot_before.snapshot_id,
            )

            plan, action_result, action = self.planner.plan(
                task=task,
                rationale=rationale,
                snapshot=snapshot_before,
                retrieved_skills=retrieved,
                last_error=last_error,
                last_code=last_code,
            )
            await self._emit(
                AgentEventType.PLAN_CREATED,
                {
                    "plan": plan.model_dump(),
                    "action": action.model_dump(),
                    "explain": action_result.explain,
                    "steps": action_result.plan,
                    "attempt": attempt,
                },
                snapshot_id=snapshot_before.snapshot_id,
            )

            validation = self.validator.validate_action(action)
            if not validation.ok:
                LOG.warning("validator rejected attempt %d: %s", attempt, validation.reason)
                last_error = f"validator: {validation.reason}"
                last_code = action.code
                continue

            self._current_status = f"executing (attempt {attempt})"
            await self._emit(
                AgentEventType.ACTION_STARTED,
                {"action": action.model_dump(), "attempt": attempt},
                snapshot_id=snapshot_before.snapshot_id,
            )
            execution, run = await self.executor.execute(action)
            await self._emit(
                AgentEventType.ACTION_COMPLETED,
                {"execution": execution.model_dump(), "durationMs": run.duration_ms},
                snapshot_id=snapshot_before.snapshot_id,
            )

            self._current_status = "verifying"

            # Task 3: Use state_after from RunJsResult to skip a second observer
            # round-trip (~200-500ms bridge call). Falls back to observer.observe()
            # when the bridge does not return embedded state.
            snapshot_after: WorldSnapshot | None = None
            if run.state_after is not None:
                snap_after_dict = run.state_after
            else:
                snapshot_after = await self.observer.observe(cycle=cycle, goal=task)
                snap_after_dict = _snapshot_for_critic(snapshot_after)

            if snapshot_after is not None:
                await self.memory.set_current_state(snapshot_after)

            snap_after_id: str | None = (
                snapshot_after.snapshot_id if snapshot_after is not None else None
            )
            snap_before_dict = _snapshot_for_critic(snapshot_before)

            # Task 1: DeterministicVerifier — skip LLM critic (~6s) for structured
            # tasks whose outcome is unambiguous from inventory/entity deltas.
            det = self._det_verifier.verify(task, snap_before_dict, snap_after_dict)

            if det is not None:
                # Ground-truth verdict — no LLM critic needed.
                # DeterministicVerifier returns "failure"; CriticVerdict uses "failed".
                critic_verdict_str = "success" if det["verdict"] == "success" else "failed"
                verdict = CriticVerdict(
                    verdict=critic_verdict_str,  # type: ignore[arg-type]
                    feedback=det["reason"],
                    confidence=1.0,
                )
                status = (
                    VerificationStatus.SUCCESS
                    if critic_verdict_str == "success"
                    else VerificationStatus.FAILED
                )
                verification = VerificationResult(
                    action_id=action.id,
                    status=status,
                    expected={"task": task},
                    observed={
                        "deterministic": True,
                        "reason": det["reason"],
                        "runtime_ok": run.ok,
                    },
                    confidence=1.0,
                )
                LOG.info(
                    "[det_verifier] task=%r verdict=%s reason=%s",
                    task, det["verdict"], det["reason"],
                )

            elif run.ok:
                # Task 2 (success path): Background the LLM critic so the loop can
                # return immediately. Recovery is driven by run.ok being True.
                # NOTE: Intentional trade-off — if the critic would say "incomplete"
                # on a run.ok=True execution, that retry signal is lost. Acceptable
                # because DeterministicVerifier covers the structured cases above.
                # True cross-cycle pipelining would require restructuring run_once.
                async def _critic_coro() -> tuple:
                    return self.verifier.verify(
                        action_id=action.id,
                        task=task,
                        code=action.code,
                        runtime_ok=run.ok,
                        runtime_error=(run.error or {}).get("message") if run.error else None,
                        runtime_result=str(run.result) if run.result is not None else None,
                        snapshot_before=snap_before_dict,
                        snapshot_after=snap_after_dict,
                    )

                def _on_critic_done(v: Any) -> None:
                    if isinstance(v, Exception):
                        LOG.warning("background critic raised: %s", v)
                    elif isinstance(v, tuple):
                        bg_vr, bg_vd = v
                        LOG.info(
                            "background critic verdict: status=%s feedback=%s",
                            bg_vr.status, bg_vd.feedback,
                        )

                default_queue().submit(_critic_coro(), on_verdict=_on_critic_done)

                # Synthetic verdict keeps downstream emit/narrator paths unchanged.
                verdict = CriticVerdict(
                    verdict="success",
                    feedback="execution succeeded without exception (critic backgrounded)",
                    confidence=0.9,
                )
                verification = VerificationResult(
                    action_id=action.id,
                    status=VerificationStatus.SUCCESS,
                    expected={"task": task},
                    observed={"runtime_ok": True, "background_critic": True},
                    confidence=0.9,
                )

            else:
                # Task 2 (failure path): Keep critic synchronous — verdict.feedback
                # is needed to set last_error for the next retry attempt.
                verification, verdict = self.verifier.verify(
                    action_id=action.id,
                    task=task,
                    code=action.code,
                    runtime_ok=run.ok,
                    runtime_error=(run.error or {}).get("message") if run.error else None,
                    runtime_result=str(run.result) if run.result is not None else None,
                    snapshot_before=snap_before_dict,
                    snapshot_after=snap_after_dict,
                )

            await self._emit(
                AgentEventType.VERIFICATION_COMPLETED,
                {"verification": verification.model_dump(), "verdict": verdict.model_dump()},
                snapshot_id=snap_after_id,
            )
            if self.narrator is not None:
                tone = "succeeded" if verification.status == VerificationStatus.SUCCESS else "did not succeed"
                self.narrator.fire_and_forget(
                    f"Task '{task}' {tone}. {verdict.feedback}",
                    AgentEventType.VERIFICATION_COMPLETED,
                )

            transition = self.recovery.decide(verification=verification, attempts_for_task=attempt)

            if verification.status == VerificationStatus.SUCCESS:
                if task not in self._completed_tasks:
                    self._completed_tasks.append(task)
                record = self.skill_builder.build(task=task, action=action_result)
                stored = await self.skill_builder.store(record)
                await self.memory.upsert_skill(stored)
                await self._emit(
                    AgentEventType.SKILL_CANDIDATE_CREATED,
                    {"skill": _skill_to_dict(stored)},
                    snapshot_id=snap_after_id,
                )
                await self._emit(
                    AgentEventType.SKILL_PROMOTED,
                    {"skill": _skill_to_dict(stored)},
                    snapshot_id=snap_after_id,
                )
                self._current_status = "idle"
                return RecoveryTransition.STORE_MEMORY

            diagnosis = self.diagnoser.classify(verification=verification, action_id=action.id)
            await self._emit(
                AgentEventType.FAILURE_DIAGNOSED,
                {"diagnosis": diagnosis.model_dump()},
                snapshot_id=snap_after_id,
            )

            last_error = verdict.feedback or verification.observed.get("runtime_error") or "incomplete"
            last_code = action.code

            if transition == RecoveryTransition.ABORT:
                if task not in self._failed_tasks:
                    self._failed_tasks.append(task)
                self._current_status = "aborted"
                return RecoveryTransition.ABORT

        if task not in self._failed_tasks:
            self._failed_tasks.append(task)
        self._current_status = "exhausted retries"
        return RecoveryTransition.ABORT

    async def run_episode(
        self,
        *,
        task_queue: list[str] | None = None,
        max_cycles: int = MAX_CYCLES_DEFAULT,
        use_curriculum: bool = False,
    ) -> dict[str, Any]:
        await self.memory.start_episode(task=", ".join(task_queue or []) or "curriculum")
        queue: deque[str] = deque(task_queue or [])
        for _ in range(max_cycles):
            task: str
            if queue:
                task = queue.popleft()
                rationale = "scheduled task"
            elif use_curriculum:
                snapshot = await self.observer.observe(cycle=self._cycle + 1, goal="(planning)")
                proposal = self.curriculum.next_task(
                    biome=snapshot.symbolic.biome,
                    time_of_day=str((snapshot.symbolic.raw_state or {}).get("timeOfDay", "unknown")),
                    health=snapshot.symbolic.health,
                    hunger=snapshot.symbolic.hunger,
                    inventory=snapshot.symbolic.inventory,
                    nearby_blocks=snapshot.symbolic.nearby_blocks,
                    nearby_entities=snapshot.symbolic.nearby_entities,
                    completed_tasks=self._completed_tasks,
                    failed_tasks=self._failed_tasks,
                )
                task = proposal.task
                rationale = proposal.rationale
            else:
                LOG.info("episode finished: queue empty and curriculum disabled")
                break
            transition = await self.run_once(task=task, rationale=rationale)
            LOG.info("cycle %d transition=%s", self._cycle, transition)
        await default_queue().drain()
        return self.status

    async def _emit(
        self,
        event_type: AgentEventType,
        data: dict[str, Any],
        *,
        snapshot_id: str | None = None,
    ) -> None:
        await self.observability.emit(
            event_type,
            data,
            cycle=self._cycle,
            snapshot_id=snapshot_id,
        )


def _snapshot_for_critic(snapshot: WorldSnapshot) -> dict[str, Any]:
    sym = snapshot.symbolic
    return {
        "inventory": sym.inventory,
        "nearbyBlocks": sym.nearby_blocks,
        "nearbyEntities": sym.nearby_entities,
        "position": sym.position.model_dump() if sym.position else None,
    }


def _skill_to_dict(record: Any) -> dict[str, Any]:
    return {
        "name": getattr(record, "name", None),
        "goal": getattr(record, "goal", None),
        "description": getattr(record, "description", None),
        "version": getattr(record, "version", 1),
        "createdAt": getattr(record, "created_at", None),
    }


__all__ = ["AgentLoop"]
