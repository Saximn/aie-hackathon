"""TDD: executor.execute() must embed wall-clock timing into evidence dict.

RED: run before implementing timing in executor.py — these will fail.
GREEN: pass once executor adds wallMs / wallSeconds to evidence.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))

from bot_client import RunJsResult
from executor import Executor
from models import JsCodeAction

pytestmark = pytest.mark.asyncio


def _make_action(**kwargs) -> JsCodeAction:
    defaults = dict(
        id="test-action-1",
        name="test_skill",
        code="bot.chat('hi')",
        timeout_ms=5000,
    )
    return JsCodeAction(**(defaults | kwargs))


def _make_run_result(ok: bool = True, duration_ms: int = 500) -> RunJsResult:
    return RunJsResult(
        ok=ok,
        result="4 logs" if ok else None,
        error=None if ok else {"message": "timeout"},
        duration_ms=duration_ms,
        state_after={"inventory": {}},
    )


async def test_evidence_contains_wallMs_on_success():
    """Evidence dict must include wallMs key with a positive integer."""
    client = MagicMock()
    client.run_js = AsyncMock(return_value=_make_run_result(ok=True, duration_ms=400))
    executor = Executor(client=client)

    result, run = await executor.execute(_make_action())

    assert result.success is True
    assert "wallMs" in result.evidence, "evidence must contain wallMs"
    assert isinstance(result.evidence["wallMs"], (int, float))
    assert result.evidence["wallMs"] >= 0


async def test_evidence_contains_wallMs_on_failure():
    """wallMs must appear in evidence even when the skill fails."""
    client = MagicMock()
    client.run_js = AsyncMock(return_value=_make_run_result(ok=False, duration_ms=60000))
    executor = Executor(client=client)

    result, run = await executor.execute(_make_action())

    assert result.success is False
    assert "wallMs" in result.evidence
    assert result.evidence["wallMs"] >= 0


async def test_evidence_preserves_existing_durationMs():
    """The bridge-reported durationMs must still be in evidence alongside wallMs."""
    client = MagicMock()
    client.run_js = AsyncMock(return_value=_make_run_result(ok=True, duration_ms=1234))
    executor = Executor(client=client)

    result, _ = await executor.execute(_make_action())

    assert result.evidence["durationMs"] == 1234
    assert "wallMs" in result.evidence


async def test_execute_logs_timing(caplog):
    """executor.execute() must emit a [timing] log line with run_js duration."""
    import logging

    client = MagicMock()
    client.run_js = AsyncMock(return_value=_make_run_result(ok=True, duration_ms=800))
    executor = Executor(client=client)

    with caplog.at_level(logging.INFO, logger="omniplay.executor"):
        await executor.execute(_make_action(name="chop_tree"))

    timing_lines = [r.message for r in caplog.records if "[timing]" in r.message]
    assert timing_lines, "expected at least one [timing] log line from executor"
