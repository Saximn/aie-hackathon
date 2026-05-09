from __future__ import annotations

import sys
from asyncio import run
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_loop import AgentLoop
from models import (
    AgentEventType,
    Diagnosis,
    FailureType,
    GameProfile,
    Plan,
    PrimitiveAction,
    PrimitiveActionType,
    RecoveryTransition,
    ResearchNote,
    WorldSnapshot,
)
from skill_builder import SkillBuilder


class FakeProfileBuilder:
    def __init__(self, initial_profile: GameProfile) -> None:
        self.initial_profile = initial_profile
        self.calls: list[tuple[str, list[ResearchNote]]] = []

    async def build(self, game_name: str, research_notes: list[ResearchNote] | None = None) -> GameProfile:
        notes = research_notes or []
        self.calls.append((game_name, notes))
        if notes:
            return self.initial_profile.model_copy(
                update={
                    "source": "researched",
                    "confidence": max(self.initial_profile.confidence, notes[0].confidence),
                    "core_mechanics": [notes[0].summary],
                },
                deep=True,
            )
        return self.initial_profile


class FakeResearcher:
    def __init__(self, note: ResearchNote | None = None) -> None:
        self.note = note or ResearchNote(
            query="",
            summary="Collect starter resources before night.",
            source_urls=["https://example.test/game"],
            confidence=0.7,
        )
        self.queries: list[str] = []

    async def research(self, query: str) -> ResearchNote:
        self.queries.append(query)
        return self.note.model_copy(update={"query": query})


class FakeObserver:
    async def observe(self, cycle: int, goal: str, game: str) -> WorldSnapshot:
        return WorldSnapshot(snapshot_id=f"{game}:{cycle}", cycle=cycle, game=game, goal=goal)


class FakePlanner:
    def __init__(self) -> None:
        self.calls = []

    async def plan(self, goal, profile, snapshot, memory_context, user_constraints=None) -> Plan:
        self.calls.append((goal, profile, snapshot, memory_context, user_constraints or []))
        return Plan(
            plan_id="plan-1",
            goal=goal,
            snapshot_id=snapshot.snapshot_id,
            actions=[
                PrimitiveAction(
                    id="wait",
                    type=PrimitiveActionType.WAIT,
                    args={"duration_ms": 1},
                    expected_result={"observable": "time passed"},
                )
            ],
        )


class FakeExecutor:
    async def execute(self, action: PrimitiveAction):
        from models import ExecutionResult

        return ExecutionResult(action_id=action.id, success=True, result="ok")


class FakeVerifier:
    async def verify(self, action, result, snapshot):
        from models import VerificationResult, VerificationStatus

        return VerificationResult(action_id=action.id, status=VerificationStatus.SUCCESS, confidence=0.9)


class FakeFailingVerifier:
    async def verify(self, action, result, snapshot):
        from models import VerificationResult, VerificationStatus

        return VerificationResult(
            action_id=action.id,
            status=VerificationStatus.FAILED,
            expected={"crafted": "torch"},
            observed={"missing": "recipe"},
            confidence=0.7,
        )


class FakeDiagnoser:
    def diagnose(self, verification):
        raise AssertionError("diagnoser should not be called for successful verification")


class FakeMissingStrategyDiagnoser:
    def diagnose(self, verification):
        return Diagnosis(
            action_id=verification.action_id,
            failure_type=FailureType.MISSING_STRATEGY,
            confidence=0.8,
            cause="repeated missing recipe knowledge",
            repair="research the early survival recipe",
            should_research=True,
            recommended_transition=RecoveryTransition.RESEARCH,
        )


class FakeMemory:
    def __init__(self) -> None:
        self.context_queries: list[str] = []
        self.research_notes: list[ResearchNote] = []
        self.skills = []
        self.events = []

    async def context(self, query: str) -> str:
        self.context_queries.append(query)
        return "remembered safe shelter preference"

    async def append_research_note(self, note: ResearchNote) -> None:
        self.research_notes.append(note)

    async def upsert_skill(self, skill) -> None:
        self.skills.append(skill)

    async def append_event(self, event) -> None:
        self.events.append(event)


def high_confidence_profile() -> GameProfile:
    return GameProfile(
        game_name="minecraft",
        genre="sandbox survival",
        core_mechanics=["Break blocks to gather resources."],
        early_game_objectives=["Collect wood."],
        source="static",
        confidence=0.95,
    )


def low_confidence_profile() -> GameProfile:
    return GameProfile(
        game_name="unknown_sandbox",
        genre="unknown",
        source="fallback",
        confidence=0.2,
    )


def test_agentloop_uses_high_confidence_profile_without_research_before_planning() -> None:
    profiles = FakeProfileBuilder(high_confidence_profile())
    researcher = FakeResearcher()
    planner = FakePlanner()
    memory = FakeMemory()

    transition = run(
        AgentLoop(
            game="minecraft",
            goal="survive_first_night",
            profile_builder=profiles,
            researcher=researcher,
            observer=FakeObserver(),
            planner=planner,
            executor=FakeExecutor(),
            verifier=FakeVerifier(),
            diagnoser=FakeDiagnoser(),
            memory_store=memory,
        ).run_once()
    )

    assert transition == RecoveryTransition.CONTINUE
    assert researcher.queries == []
    assert profiles.calls == [("minecraft", [])]
    assert planner.calls[0][1].confidence == 0.95
    assert planner.calls[0][3] == "remembered safe shelter preference"


def test_agentloop_researches_low_confidence_profile_before_planning_and_persists_note() -> None:
    profiles = FakeProfileBuilder(low_confidence_profile())
    researcher = FakeResearcher(
        ResearchNote(
            query="",
            summary="Collect wood, craft light, and build shelter before night.",
            source_urls=["https://example.test/unknown-sandbox"],
            confidence=0.74,
        )
    )
    planner = FakePlanner()
    memory = FakeMemory()

    loop = AgentLoop(
        game="unknown_sandbox",
        goal="survive_first_night",
        profile_builder=profiles,
        researcher=researcher,
        observer=FakeObserver(),
        planner=planner,
        executor=FakeExecutor(),
        verifier=FakeVerifier(),
        diagnoser=FakeDiagnoser(),
        skill_builder=SkillBuilder(),
        memory_store=memory,
    )

    transition = run(loop.run_once())

    assert transition == RecoveryTransition.CONTINUE
    assert len(researcher.queries) == 1
    assert profiles.calls[0] == ("unknown_sandbox", [])
    assert profiles.calls[1][0] == "unknown_sandbox"
    assert (
        profiles.calls[1][1][0].summary
        == "Collect wood, craft light, and build shelter before night."
    )
    assert planner.calls[0][1].source == "researched"
    assert planner.calls[0][1].core_mechanics == ["Collect wood, craft light, and build shelter before night."]
    assert memory.research_notes == profiles.calls[1][1]
    research_events = [
        event.event_type
        for event in loop.events
        if event.event_type in {AgentEventType.RESEARCH_STARTED, AgentEventType.RESEARCH_COMPLETED}
    ]
    assert research_events == [
        AgentEventType.RESEARCH_STARTED,
        AgentEventType.RESEARCH_COMPLETED,
    ]
    assert memory.skills[0].source == "researched"
    assert memory.skills[0].status == "candidate"
    assert not hasattr(memory.skills[0], "script")


def test_agentloop_researches_incomplete_profile_even_when_confidence_is_high() -> None:
    profile = GameProfile(
        game_name="custom_survival",
        genre="sandbox survival",
        core_mechanics=[],
        early_game_objectives=[],
        source="static",
        confidence=0.9,
    )
    researcher = FakeResearcher()

    transition = run(
        AgentLoop(
            game="custom_survival",
            goal="survive_first_night",
            profile_builder=FakeProfileBuilder(profile),
            researcher=researcher,
            observer=FakeObserver(),
            planner=FakePlanner(),
            executor=FakeExecutor(),
            verifier=FakeVerifier(),
            diagnoser=FakeDiagnoser(),
            memory_store=FakeMemory(),
        ).run_once()
    )

    assert transition == RecoveryTransition.CONTINUE
    assert len(researcher.queries) == 1


def test_agentloop_researches_after_repeated_missing_strategy_diagnosis() -> None:
    researcher = FakeResearcher(
        ResearchNote(
            query="",
            summary="Craft torches from sticks and coal before night exploration.",
            source_urls=["https://example.test/torch"],
            confidence=0.82,
        )
    )
    memory = FakeMemory()
    loop = AgentLoop(
        game="minecraft",
        goal="craft_torch",
        profile_builder=FakeProfileBuilder(high_confidence_profile()),
        researcher=researcher,
        observer=FakeObserver(),
        planner=FakePlanner(),
        executor=FakeExecutor(),
        verifier=FakeFailingVerifier(),
        diagnoser=FakeMissingStrategyDiagnoser(),
        memory_store=memory,
    )

    transition = run(loop.run_once())

    assert transition == RecoveryTransition.RESEARCH
    assert len(researcher.queries) == 1
    assert "missing_strategy" in researcher.queries[0]
    assert (
        memory.research_notes[0].summary
        == "Craft torches from sticks and coal before night exploration."
    )
    research_events = [
        event.event_type
        for event in loop.events
        if event.event_type in {AgentEventType.RESEARCH_STARTED, AgentEventType.RESEARCH_COMPLETED}
    ]
    assert research_events == [AgentEventType.RESEARCH_STARTED, AgentEventType.RESEARCH_COMPLETED]
