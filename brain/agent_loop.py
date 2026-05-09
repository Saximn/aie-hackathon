"""AgentLoop orchestration scaffold."""

from __future__ import annotations

from uuid import uuid4

from diagnoser import Diagnoser
from event_bus import EventBus
from executor import Executor
from game_profile_builder import GameProfileBuilder
from memory_store import MemoryStore
from models import AgentEvent, AgentEventType, PrimitiveAction, RecoveryTransition
from observer import Observer
from planner import Planner
from recovery_policy import RecoveryPolicy
from skill_builder import SkillBuilder
from validator import Validator
from verifier import Verifier


class AgentLoop:
    """Owns sequencing, retries, replanning, research, and memory updates."""

    def __init__(
        self,
        profile_builder: GameProfileBuilder,
        observer: Observer,
        planner: Planner,
        validator: Validator,
        executor: Executor,
        verifier: Verifier,
        diagnoser: Diagnoser,
        recovery_policy: RecoveryPolicy,
        skill_builder: SkillBuilder,
        memory_store: MemoryStore,
        event_bus: EventBus,
    ) -> None:
        self.profile_builder = profile_builder
        self.observer = observer
        self.planner = planner
        self.validator = validator
        self.executor = executor
        self.verifier = verifier
        self.diagnoser = diagnoser
        self.recovery_policy = recovery_policy
        self.skill_builder = skill_builder
        self.memory_store = memory_store
        self.event_bus = event_bus
        self.cycle = 0

    async def run_once(
        self,
        goal: str = "survive_first_night",
        game_name: str = "minecraft",
        user_constraints: list[str] | None = None,
    ) -> RecoveryTransition:
        """Run one slow OmniForge cycle.

        The loop intentionally owns all component sequencing. Subcomponents
        return structured data and do not call each other directly.
        """
        self.cycle += 1
        await self._emit(AgentEventType.GOAL_RECEIVED, {"goal": goal, "game": game_name})

        profile = await self.profile_builder.build(game_name)
        await self._emit(AgentEventType.GAME_PROFILE_CREATED, profile.model_dump(mode="json"))

        snapshot = await self.observer.observe(cycle=self.cycle, goal=goal, game=profile.game_name)
        await self._emit(
            AgentEventType.WORLD_OBSERVED,
            snapshot.model_dump(mode="json"),
            snapshot_id=snapshot.snapshot_id,
        )

        memory_context = await self.memory_store.context()
        await self._emit(AgentEventType.MEMORY_RETRIEVED, {"summary": memory_context})

        plan = await self.planner.plan(
            goal=goal,
            profile=profile,
            snapshot=snapshot,
            memory_context=memory_context,
            user_constraints=user_constraints or [],
        )
        await self._emit(AgentEventType.PLAN_CREATED, plan.model_dump(mode="json"), snapshot.snapshot_id)

        validation = self.validator.validate_plan(plan)
        if validation.status == RecoveryTransition.ABORT:
            await self._emit(AgentEventType.FAILURE_DIAGNOSED, {"reason": validation.reason})
            return RecoveryTransition.ABORT

        transition = RecoveryTransition.CONTINUE
        for action in plan.actions:
            transition = await self._run_action(action, goal, profile.game_name, snapshot.snapshot_id)
            if transition not in {RecoveryTransition.CONTINUE, RecoveryTransition.STORE_MEMORY}:
                return transition

        if plan.actions:
            skill = self.skill_builder.from_plan(plan, source="learned")
            await self.memory_store.upsert_skill(skill)
            await self._emit(AgentEventType.SKILL_CANDIDATE_CREATED, skill.model_dump(mode="json"))
            return RecoveryTransition.STORE_MEMORY

        return transition

    async def _run_action(
        self,
        action: PrimitiveAction,
        goal: str,
        game_name: str,
        snapshot_id: str,
    ) -> RecoveryTransition:
        await self._emit(AgentEventType.ACTION_STARTED, action.model_dump(mode="json"), snapshot_id)
        execution = await self.executor.execute(action)
        await self._emit(AgentEventType.ACTION_COMPLETED, execution.model_dump(mode="json"), snapshot_id)

        post_snapshot = await self.observer.observe(cycle=self.cycle, goal=goal, game=game_name)
        verification = self.verifier.verify(action, execution, post_snapshot)
        await self._emit(
            AgentEventType.VERIFICATION_COMPLETED,
            verification.model_dump(mode="json"),
            post_snapshot.snapshot_id,
        )

        if verification.status.value == "success":
            return RecoveryTransition.CONTINUE

        diagnosis = self.diagnoser.diagnose(verification)
        await self._emit(
            AgentEventType.FAILURE_DIAGNOSED,
            diagnosis.model_dump(mode="json"),
            post_snapshot.snapshot_id,
        )
        return self.recovery_policy.recommend(verification, diagnosis)

    async def _emit(
        self,
        event_type: AgentEventType,
        data: dict,
        snapshot_id: str | None = None,
    ) -> None:
        event = AgentEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            cycle=self.cycle,
            snapshot_id=snapshot_id,
            data=data,
        )
        await self.event_bus.publish(event)
        await self.memory_store.append_event(event)
