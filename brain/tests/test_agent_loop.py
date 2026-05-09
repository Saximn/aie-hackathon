from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_loop import AgentLoop
from event_bus import EventBus
from models import (
    AdapterKind,
    AgentEventType,
    Diagnosis,
    ExecutionResult,
    FailureType,
    GameProfile,
    Plan,
    PrimitiveAction,
    PrimitiveActionType,
    RecoveryTransition,
    ResearchNote,
    VerificationResult,
    VerificationStatus,
    VisualObservation,
    WorldSnapshot,
)


class FakeProfileBuilder:
    async def build(self, game_name: str, research_notes=None) -> GameProfile:
        return GameProfile(
            game_name=game_name,
            genre="sandbox survival",
            controls={"move": "WASD"},
            core_mechanics=["Collect wood before night."],
            early_game_objectives=["Collect wood."],
            benchmark_goals=["survive_first_night"],
            adapter_hints=[AdapterKind.GENERIC_INPUT],
            source="static",
            confidence=0.95,
        )


class FakeObserver:
    async def observe(self, cycle: int, goal: str, game: str) -> WorldSnapshot:
        return WorldSnapshot(
            snapshot_id=f"{game}:{cycle}",
            cycle=cycle,
            game=game,
            goal=goal,
            visual=VisualObservation(visible_objects=["tree"], risk_level="low", confidence=0.9),
        )


class FakePlanner:
    async def plan(self, goal, profile, snapshot, memory_context, user_constraints=None) -> Plan:
        return Plan(
            plan_id="plan-1",
            goal=goal,
            snapshot_id=snapshot.snapshot_id,
            actions=[
                PrimitiveAction(
                    id="approach_tree",
                    type=PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT,
                    args={"object": "tree"},
                    expected_result={"visible_object": "tree"},
                )
            ],
        )


class FakeExecutor:
    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        return ExecutionResult(action_id=action.id, success=True, result="ok")


class FakeMemoryStore:
    def __init__(self) -> None:
        self.events = []
        self.skills = []

    async def context(self, query: str = "relevant OmniForge agent memories") -> str:
        return "remembered safe opening"

    async def append_event(self, event) -> None:
        self.events.append(event)

    async def upsert_skill(self, skill) -> None:
        self.skills.append(skill)

    async def append_research_note(self, note) -> None:
        self.research_note = note

    async def upsert_game_profile(self, profile) -> None:
        self.game_profile = profile


def test_agent_loop_runs_static_profile_plan_path() -> None:
    import asyncio

    event_bus = EventBus()
    memory = FakeMemoryStore()
    loop = AgentLoop(
        game="minecraft",
        goal="survive_first_night",
        profile_builder=FakeProfileBuilder(),
        observer=FakeObserver(),
        planner=FakePlanner(),
        executor=FakeExecutor(),
        memory_store=memory,
        event_bus=event_bus,
    )

    transition = asyncio.run(loop.run_once())

    assert transition == RecoveryTransition.CONTINUE
    assert loop.status.cycle == 1
    assert loop.status.transition == RecoveryTransition.CONTINUE
    assert [event.event_type for event in event_bus.events] == [
        AgentEventType.GOAL_RECEIVED,
        AgentEventType.GAME_PROFILE_CREATED,
        AgentEventType.WORLD_OBSERVED,
        AgentEventType.MEMORY_RETRIEVED,
        AgentEventType.PLAN_CREATED,
        AgentEventType.ACTION_STARTED,
        AgentEventType.ACTION_COMPLETED,
        AgentEventType.VERIFICATION_COMPLETED,
        AgentEventType.SKILL_CANDIDATE_CREATED,
    ]
    assert memory.skills[0].goal == "survive_first_night"


def test_agent_loop_researches_unknown_profile_before_planning() -> None:
    import asyncio

    class LowConfidenceProfileBuilder:
        def __init__(self) -> None:
            self.notes_seen = []

        async def build(self, game_name: str, research_notes=None) -> GameProfile:
            self.notes_seen.append(research_notes or [])
            if research_notes:
                return GameProfile(
                    game_name=game_name,
                    genre="sandbox survival",
                    core_mechanics=["Use researched survival notes."],
                    source="researched",
                    confidence=0.7,
                )
            return GameProfile(game_name=game_name, genre="unknown", source="fallback", confidence=0.15)

    class FakeResearcher:
        async def research(self, query: str) -> ResearchNote:
            return ResearchNote(
                query=query,
                summary="Use WASD and collect wood early.",
                source_urls=["https://example.test/guide"],
                confidence=0.7,
            )

    event_bus = EventBus()
    memory = FakeMemoryStore()
    profile_builder = LowConfidenceProfileBuilder()
    loop = AgentLoop(
        game="veloren",
        goal="survive_first_night",
        profile_builder=profile_builder,
        observer=FakeObserver(),
        planner=FakePlanner(),
        executor=FakeExecutor(),
        researcher=FakeResearcher(),
        memory_store=memory,
        event_bus=event_bus,
    )

    transition = asyncio.run(loop.run_once())

    assert transition == RecoveryTransition.CONTINUE
    assert len(profile_builder.notes_seen[1]) == 1
    assert memory.research_note.summary == "Use WASD and collect wood early."
    assert memory.game_profile.source == "researched"
    assert AgentEventType.RESEARCH_STARTED in [event.event_type for event in event_bus.events]
    assert AgentEventType.RESEARCH_COMPLETED in [event.event_type for event in event_bus.events]


def test_agent_loop_researches_missing_strategy_failure() -> None:
    import asyncio

    class FailingVerifier:
        def verify(self, action, result, post_snapshot) -> VerificationResult:
            return VerificationResult(
                action_id=action.id,
                status=VerificationStatus.FAILED,
                expected={"crafted": "shelter"},
                observed={"missing": "strategy"},
                confidence=0.8,
            )

    class MissingStrategyDiagnoser:
        def diagnose(self, verification: VerificationResult) -> Diagnosis:
            return Diagnosis(
                action_id=verification.action_id,
                failure_type=FailureType.MISSING_STRATEGY,
                confidence=0.8,
                cause="The plan lacks a shelter strategy.",
                repair="Research first-night shelter strategy.",
                should_research=True,
                recommended_transition=RecoveryTransition.REPLAN,
            )

    class FakeResearcher:
        async def research(self, query: str) -> ResearchNote:
            return ResearchNote(query=query, summary="Build a small shelter before night.", confidence=0.6)

    event_bus = EventBus()
    memory = FakeMemoryStore()
    loop = AgentLoop(
        game="minecraft",
        goal="survive_first_night",
        profile_builder=FakeProfileBuilder(),
        observer=FakeObserver(),
        planner=FakePlanner(),
        executor=FakeExecutor(),
        verifier=FailingVerifier(),
        diagnoser=MissingStrategyDiagnoser(),
        researcher=FakeResearcher(),
        memory_store=memory,
        event_bus=event_bus,
    )

    transition = asyncio.run(loop.run_once())

    assert transition == RecoveryTransition.RESEARCH
    assert memory.research_note.summary == "Build a small shelter before night."
    event_types = [event.event_type for event in event_bus.events]
    assert AgentEventType.RESEARCH_STARTED in event_types
    assert AgentEventType.RESEARCH_COMPLETED in event_types
    assert event_types[-1] == AgentEventType.SKILL_CANDIDATE_CREATED


def test_agent_loop_researches_explicit_user_coaching_question() -> None:
    import asyncio

    class FakeResearcher:
        async def research(self, query: str) -> ResearchNote:
            return ResearchNote(query=query, summary="Craft planks from collected wood.", confidence=0.7)

    event_bus = EventBus()
    memory = FakeMemoryStore()
    loop = AgentLoop(
        game="minecraft",
        goal="survive_first_night",
        user_constraints=["How do I craft planks?"],
        profile_builder=FakeProfileBuilder(),
        observer=FakeObserver(),
        planner=FakePlanner(),
        executor=FakeExecutor(),
        researcher=FakeResearcher(),
        memory_store=memory,
        event_bus=event_bus,
    )

    transition = asyncio.run(loop.run_once())

    assert transition == RecoveryTransition.CONTINUE
    assert "How do I craft planks?" in memory.research_note.query
    assert AgentEventType.RESEARCH_STARTED in [event.event_type for event in event_bus.events]
