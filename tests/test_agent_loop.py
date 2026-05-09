"""Lightweight tests for the current AgentLoop API (OmniPlay-MC Voyager build).

All heavy I/O dependencies (BotClient, SkillManager, MemoryStore, Planner,
Executor, Verifier, Validator, SkillBuilder) are replaced with in-process
fakes so no bridge, Chroma, Convex, or LLM calls are made.

Choosing Option B: brain/tests/test_agent_loop.py is stale (uses the old
OmniForge API with game=, goal=, run_once() no-arg, etc.) and is not
migrated here because the old and new APIs differ fundamentally.  The old
file remains ignored via --ignore=brain/tests in pytest.ini.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "brain"))

from bot_client import RunJsResult
from models import (
    AgentEventType,
    ExecutionResult,
    JsCodeAction,
    Plan,
    RecoveryTransition,
    VerificationResult,
    VerificationStatus,
    WorldSnapshot,
)
from voyager_agents.action import ActionResult
from voyager_agents.skill import SkillRecord

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeBotClient:
    async def get_state(self) -> dict[str, Any]:
        return {
            "health": 20,
            "hunger": 20,
            "inventory": {"oak_log": 3},
            "nearbyBlocks": ["oak_log", "dirt", "grass"],
            "nearbyEntities": [],
            "biome": "forest",
        }

    async def run_js(self, code: str, *, timeout_ms: int = 5000) -> RunJsResult:
        return RunJsResult(ok=True, result="done", error=None, duration_ms=10, state_after=None)


class FakeSkillManager:
    def __init__(self) -> None:
        self.upserted: list[SkillRecord] = []

    def count(self) -> int:
        return 0

    def retrieve(self, query: str, *, k: int = 3):
        return []

    def upsert(self, record: SkillRecord) -> SkillRecord:
        self.upserted.append(record)
        return record


class FakeMemoryStore:
    def __init__(self) -> None:
        self.upserted_skills: list[SkillRecord] = []

    async def start_episode(self, *, task: str) -> None:
        pass

    async def set_current_state(self, snapshot: WorldSnapshot) -> None:
        pass

    async def upsert_skill(self, record: SkillRecord) -> None:
        self.upserted_skills.append(record)

    async def add_lesson(self, **kwargs: Any) -> None:
        pass


class FakePlanner:
    def plan(
        self,
        *,
        task: str,
        rationale: str,
        snapshot: WorldSnapshot,
        retrieved_skills: list,
        last_error: str | None = None,
        last_code: str | None = None,
    ) -> tuple[Plan, ActionResult, JsCodeAction]:
        action_result = ActionResult(
            explain="Chop the nearest oak log.",
            plan=["approach tree", "chop"],
            code="await bot.dig(bot.findBlock({matching: mcData.blocksByName['oak_log'].id}));",
            name="chop_oak_log",
        )
        action = JsCodeAction(
            id=uuid.uuid4().hex,
            name="chop_oak_log",
            description="Chop an oak log.",
            code=action_result.code,
            expected_outcome=task,
        )
        plan = Plan(
            plan_id=uuid.uuid4().hex,
            goal=task,
            snapshot_id=snapshot.snapshot_id,
            used_skills=[],
            actions=[],
        )
        return plan, action_result, action


class FakeValidator:
    def validate_action(self, action: JsCodeAction):
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class _VR:
            ok: bool = True
            status: RecoveryTransition = RecoveryTransition.CONTINUE
            reason: str = ""

        return _VR()


class FakeVerifier:
    def verify(self, **kwargs: Any) -> tuple[VerificationResult, Any]:
        from voyager_agents.critic import CriticVerdict

        verdict = CriticVerdict(verdict="success", confidence=0.95, feedback="Task completed.")
        verification = VerificationResult(
            action_id=kwargs["action_id"],
            status=VerificationStatus.SUCCESS,
            expected={"task": kwargs["task"]},
            observed={"runtime_ok": True},
            confidence=0.95,
        )
        return verification, verdict


class FakeExecutor:
    async def execute(self, action: JsCodeAction) -> tuple[ExecutionResult, RunJsResult]:
        run = RunJsResult(ok=True, result="done", error=None, duration_ms=50, state_after=None)
        result = ExecutionResult(action_id=action.id, success=True, result="done", evidence={})
        return result, run


class FakeDeterministicVerifier:
    """Always returns None so the FakeVerifier handles all verdicts."""

    def can_verify(self, task: str) -> bool:
        return False

    def verify(self, task: str, snapshot_before: dict, snapshot_after: dict):
        return None


class FakeSkillBuilder:
    def __init__(self, skill_manager: FakeSkillManager) -> None:
        self.skill_manager = skill_manager

    def build(self, *, task: str, action: ActionResult) -> SkillRecord:
        return SkillRecord(
            name="chop_oak_log",
            goal=task,
            code=action.code,
            description=action.explain or task,
        )

    async def store(self, record: SkillRecord) -> SkillRecord:
        return self.skill_manager.upsert(record)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _make_loop(
    memory: FakeMemoryStore | None = None,
    skill_manager: FakeSkillManager | None = None,
) -> tuple[Any, FakeMemoryStore, FakeSkillManager]:
    """Construct a fully-mocked AgentLoop."""
    from agent_loop import AgentLoop
    from event_bus import EventBus

    sm = skill_manager or FakeSkillManager()
    mem = memory or FakeMemoryStore()
    loop = AgentLoop(
        bot_client=FakeBotClient(),
        skill_manager=sm,
        memory=mem,
        event_bus=EventBus(),
        planner=FakePlanner(),
        executor=FakeExecutor(),
        verifier=FakeVerifier(),
        validator=FakeValidator(),
        skill_builder=FakeSkillBuilder(sm),
        det_verifier=FakeDeterministicVerifier(),
    )
    return loop, mem, sm


def test_agent_loop_constructs_with_required_args() -> None:
    loop, _, _ = _make_loop()
    assert loop is not None


def test_agent_loop_status_is_dict_with_cycle_key() -> None:
    loop, _, _ = _make_loop()
    status = loop.status
    assert isinstance(status, dict)
    assert "cycle" in status
    assert status["cycle"] == 0


def test_run_once_returns_store_memory_on_success() -> None:
    loop, _, _ = _make_loop()
    transition = asyncio.run(loop.run_once(task="collect oak_log", rationale="test"))
    assert transition == RecoveryTransition.STORE_MEMORY


def test_run_once_increments_cycle() -> None:
    loop, _, _ = _make_loop()
    asyncio.run(loop.run_once(task="collect oak_log", rationale="test"))
    assert loop.status["cycle"] == 1


def test_run_once_records_skill_on_success() -> None:
    sm = FakeSkillManager()
    mem = FakeMemoryStore()
    loop, mem, sm = _make_loop(memory=mem, skill_manager=sm)
    asyncio.run(loop.run_once(task="collect oak_log", rationale="test"))
    assert len(sm.upserted) == 1
    assert sm.upserted[0].goal == "collect oak_log"


def test_run_once_adds_task_to_completed() -> None:
    loop, _, _ = _make_loop()
    asyncio.run(loop.run_once(task="collect oak_log", rationale="test"))
    assert "collect oak_log" in loop.status["completed"]


def test_run_episode_with_task_queue_runs_one_cycle() -> None:
    loop, _, sm = _make_loop()
    result = asyncio.run(
        loop.run_episode(task_queue=["collect oak_log"], max_cycles=1)
    )
    assert isinstance(result, dict)
    assert result["cycle"] == 1
    assert len(sm.upserted) == 1


def test_run_episode_empty_queue_runs_zero_cycles() -> None:
    loop, _, _ = _make_loop()
    result = asyncio.run(loop.run_episode(task_queue=[], max_cycles=10))
    assert result["cycle"] == 0
