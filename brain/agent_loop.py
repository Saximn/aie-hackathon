"""AgentLoop orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from diagnoser import Diagnoser
from event_bus import EventBus
from executor import Executor
from game_profile_builder import GameProfileBuilder
from memory_store import MemoryStore
from models import (
    AgentEvent,
    AgentEventType,
    AgentLoopStatus,
    Diagnosis,
    GameProfile,
    RecoveryTransition,
    ResearchNote,
    TrackStatus,
    VerificationResult,
    VerificationStatus,
)
from observer import Observer
from planner import Planner
from recovery_policy import RecoveryPolicy
from researcher import Researcher
from skill_builder import SkillBuilder
from validator import Validator


class AgentLoop:
    """Owns sequencing, retries, replanning, research, and memory updates."""

    def __init__(
        self,
        game: str = "minecraft",
        goal: str = "survive_first_night",
        user_constraints: list[str] | None = None,
        max_cycles: int = 1,
        research_allowed: bool = True,
        profile_builder: Any | None = None,
        observer: Any | None = None,
        planner: Any | None = None,
        validator: Validator | None = None,
        executor: Any | None = None,
        verifier: Any | None = None,
        diagnoser: Diagnoser | None = None,
        recovery_policy: RecoveryPolicy | None = None,
        researcher: Researcher | None = None,
        skill_builder: SkillBuilder | None = None,
        memory_store: Any | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.game = game
        self.goal = goal
        self.user_constraints = user_constraints or []
        self.max_cycles = max(1, max_cycles)
        self.research_allowed = research_allowed
        self.profile_builder = profile_builder or GameProfileBuilder()
        self.observer = observer or Observer()
        self.planner = planner or Planner()
        self.validator = validator or Validator()
        self.executor = executor or Executor()
        from verifier import Verifier

        self.verifier = verifier or Verifier()
        self.diagnoser = diagnoser or Diagnoser()
        self.recovery_policy = recovery_policy or RecoveryPolicy()
        self.researcher = researcher or Researcher()
        self.skill_builder = skill_builder or SkillBuilder()
        self.memory_store = memory_store or MemoryStore()
        self.event_bus = event_bus or EventBus()
        self._status = AgentLoopStatus(
            running=True,
            game=game,
            goal=goal,
            cycle=0,
            tracks={
                "runtime": TrackStatus.UNKNOWN,
                "observation": TrackStatus.UNKNOWN,
                "planning": TrackStatus.READY,
                "research": TrackStatus.READY if research_allowed else TrackStatus.UNAVAILABLE,
                "memory": TrackStatus.UNKNOWN,
            },
        )

    @property
    def status(self) -> AgentLoopStatus:
        """Return the latest AgentLoop status."""
        return self._status

    async def run_once(self) -> RecoveryTransition:
        """Run one OmniForge cycle through public module interfaces."""
        cycle = self._status.cycle + 1
        await self._publish(AgentEventType.GOAL_RECEIVED, cycle, {"game": self.game, "goal": self.goal})

        profile = await self.profile_builder.build(self.game)
        profile = await self._research_profile_if_needed(profile, cycle)
        await self._publish(
            AgentEventType.GAME_PROFILE_CREATED,
            cycle,
            {"profile": profile.model_dump(mode="json")},
        )

        snapshot = await self.observer.observe(cycle=cycle, goal=self.goal, game=profile.game_name)
        await self._publish(
            AgentEventType.WORLD_OBSERVED,
            cycle,
            {"snapshot": snapshot.model_dump(mode="json")},
            snapshot_id=snapshot.snapshot_id,
        )

        memory_context = await self._memory_context()
        await self._publish(
            AgentEventType.MEMORY_RETRIEVED,
            cycle,
            {"available": bool(memory_context), "context": memory_context},
            snapshot_id=snapshot.snapshot_id,
        )

        plan = await self.planner.plan(
            self.goal,
            profile,
            snapshot,
            memory_context,
            self.user_constraints,
        )
        await self._publish(
            AgentEventType.PLAN_CREATED,
            cycle,
            {"plan": plan.model_dump(mode="json")},
            snapshot_id=snapshot.snapshot_id,
        )

        validation = self.validator.validate_plan(plan)
        if validation.status != RecoveryTransition.CONTINUE:
            return await self._finish(cycle, validation.status, {"reason": validation.reason})

        for action in plan.actions:
            await self._publish(
                AgentEventType.ACTION_STARTED,
                cycle,
                {"action": action.model_dump(mode="json")},
                snapshot_id=snapshot.snapshot_id,
            )
            execution = await self.executor.execute(action)
            await self._publish(
                AgentEventType.ACTION_COMPLETED,
                cycle,
                {"execution": execution.model_dump(mode="json")},
                snapshot_id=snapshot.snapshot_id,
            )

            post_snapshot = await self.observer.observe(cycle=cycle, goal=self.goal, game=profile.game_name)
            verification = self.verifier.verify(action, execution, post_snapshot)
            await self._publish(
                AgentEventType.VERIFICATION_COMPLETED,
                cycle,
                {"verification": verification.model_dump(mode="json")},
                snapshot_id=post_snapshot.snapshot_id,
            )

            if verification.status != VerificationStatus.SUCCESS:
                return await self._recover(cycle, verification)

        skill = self.skill_builder.from_plan(plan)
        await self._safe_memory_call("upsert_skill", skill)
        await self._publish(
            AgentEventType.SKILL_CANDIDATE_CREATED,
            cycle,
            {"skill": skill.model_dump(mode="json")},
            snapshot_id=snapshot.snapshot_id,
        )
        return await self._finish(cycle, RecoveryTransition.CONTINUE)

    async def _research_profile_if_needed(self, profile: GameProfile, cycle: int) -> GameProfile:
        if not self.research_allowed:
            return profile

        coaching_query = _coaching_research_query(self.game, self.goal, self.user_constraints)
        if coaching_query:
            note = await self._research(cycle, coaching_query)
            await self._safe_memory_call("append_research_note", note)
            await self._store_guidance_skill(note, cycle)
            if note.confidence > 0:
                profile = await self.profile_builder.build(profile.game_name, [note])
                await self._safe_memory_call("upsert_game_profile", profile)
            return profile

        if profile.confidence >= 0.4:
            return profile

        query = f"{profile.game_name} early survival controls mechanics first night"
        note = await self._research(cycle, query)
        if note.confidence <= 0:
            return profile

        await self._safe_memory_call("append_research_note", note)
        await self._store_guidance_skill(note, cycle)
        researched_profile = await self.profile_builder.build(profile.game_name, [note])
        await self._safe_memory_call("upsert_game_profile", researched_profile)
        return researched_profile

    async def _recover(self, cycle: int, verification: VerificationResult) -> RecoveryTransition:
        diagnosis = self.diagnoser.diagnose(verification)
        transition = self.recovery_policy.recommend(verification, diagnosis)
        await self._publish(
            AgentEventType.FAILURE_DIAGNOSED,
            cycle,
            {"diagnosis": diagnosis.model_dump(mode="json"), "transition": transition},
        )

        if transition == RecoveryTransition.RESEARCH and self.research_allowed:
            note = await self._research(cycle, _research_query_from_diagnosis(self.game, self.goal, diagnosis))
            await self._safe_memory_call("append_research_note", note)
            await self._store_guidance_skill(note, cycle)

        return await self._finish(cycle, transition)

    async def _store_guidance_skill(self, note: ResearchNote, cycle: int) -> None:
        if note.confidence <= 0:
            return

        skill = self.skill_builder.from_guidance(self.goal, note)
        await self._safe_memory_call("upsert_skill", skill)
        await self._publish(
            AgentEventType.SKILL_CANDIDATE_CREATED,
            cycle,
            {"skill": skill.model_dump(mode="json"), "source_note": note.query},
        )

    async def _research(self, cycle: int, query: str) -> ResearchNote:
        await self._publish(AgentEventType.RESEARCH_STARTED, cycle, {"query": query})
        note = await self.researcher.research(query)
        await self._publish(
            AgentEventType.RESEARCH_COMPLETED,
            cycle,
            {"note": note.model_dump(mode="json")},
        )
        return note

    async def _memory_context(self) -> str:
        try:
            context = await self.memory_store.context(f"{self.game} {self.goal}")
        except Exception:
            self._set_track("memory", TrackStatus.UNAVAILABLE)
            return ""

        self._set_track("memory", TrackStatus.READY)
        return context

    async def _safe_memory_call(self, method_name: str, *args: Any) -> None:
        method = getattr(self.memory_store, method_name, None)
        if method is None:
            return
        try:
            await method(*args)
        except Exception:
            self._set_track("memory", TrackStatus.UNAVAILABLE)

    async def _publish(
        self,
        event_type: AgentEventType,
        cycle: int,
        data: dict[str, Any],
        snapshot_id: str | None = None,
    ) -> None:
        event = AgentEvent(
            id=str(uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
            event_type=event_type,
            cycle=cycle,
            snapshot_id=snapshot_id,
            data=data,
        )
        await self.event_bus.publish(event)
        await self._safe_memory_call("append_event", event)
        self._status = self._status.model_copy(update={"last_event_id": event.id})

    async def _finish(
        self,
        cycle: int,
        transition: RecoveryTransition,
        data: dict[str, Any] | None = None,
    ) -> RecoveryTransition:
        self._status = self._status.model_copy(
            update={
                "cycle": cycle,
                "transition": transition,
                "running": cycle < self.max_cycles and transition == RecoveryTransition.CONTINUE,
            }
        )
        if data:
            self._status.tracks["planning"] = TrackStatus.DEGRADED
        return transition

    def _set_track(self, name: str, status: TrackStatus) -> None:
        tracks = dict(self._status.tracks)
        tracks[name] = status
        self._status = self._status.model_copy(update={"tracks": tracks})


def _research_query_from_diagnosis(game: str, goal: str, diagnosis: Diagnosis) -> str:
    parts = [game, goal, str(diagnosis.failure_type or ""), diagnosis.cause, diagnosis.repair]
    return " ".join(part for part in parts if part).strip()


def _coaching_research_query(game: str, goal: str, user_constraints: list[str]) -> str:
    coaching = [
        constraint
        for constraint in user_constraints
        if "?" in constraint
        or constraint.lower().startswith(("how ", "what ", "where ", "research ", "learn "))
    ]
    if not coaching:
        return ""
    return f"{game} {goal} user coaching: {' '.join(coaching)}"
