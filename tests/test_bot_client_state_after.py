"""Slice 4 (TDD): ``BotClient.run_js`` must surface ``stateAfter``.

The Mineflayer bridge already returns the post-execution world state alongside
each ``runJs`` result.  Surfacing it on :class:`RunJsResult` lets the loop
skip the extra ``observer.observe()`` round-trip after each successful action
(saves ~0.3-0.5s/cycle).

RED:  the field may be absent or unparsed.
GREEN: ``RunJsResult.state_after`` carries the bridge dict (or ``None`` if
       absent), no extra bridge calls are issued.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))

from bot_client import BotClient, RunJsResult


def _stub_call(client: BotClient, response: dict):
    """Patch ``BotClient.call`` so ``run_js`` resolves with *response*.

    Returns a synchronous context manager — use ``with`` (not ``async with``)
    because :func:`unittest.mock.patch.object` is a sync CM even though the
    patched method is async.
    """
    return patch.object(
        client,
        "call",
        new=AsyncMock(return_value=response),
    )


# ---------------------------------------------------------------------------
# Field shape
# ---------------------------------------------------------------------------

def test_run_js_result_has_state_after_field():
    """RunJsResult must declare a ``state_after`` field (so the loop can read it)."""
    result = RunJsResult(
        ok=True,
        result="ok",
        error=None,
        duration_ms=10,
        state_after={"inventory": {"oak_log": 4}},
    )
    assert hasattr(result, "state_after")
    assert result.state_after == {"inventory": {"oak_log": 4}}


# ---------------------------------------------------------------------------
# run_js parses stateAfter from the bridge response
# ---------------------------------------------------------------------------

async def test_run_js_returns_state_after_when_present():
    """When the bridge sends ``stateAfter``, ``RunJsResult.state_after`` is populated."""
    client = BotClient()
    bridge_state = {
        "inventory": {"oak_log": 4, "oak_planks": 0},
        "position": {"x": 12, "y": 64, "z": -7},
        "nearbyBlocks": ["dirt", "grass"],
        "nearbyEntities": [],
    }
    bridge_response = {
        "ok": True,
        "result": "chopped 4 logs",
        "error": None,
        "durationMs": 1234,
        "stateAfter": bridge_state,
    }
    with _stub_call(client, bridge_response):
        run = await client.run_js("await bot.chat('hi')", timeout_ms=5_000)

    assert isinstance(run, RunJsResult)
    assert run.ok is True
    assert run.duration_ms == 1234
    assert run.state_after == bridge_state, (
        f"state_after must mirror bridge.stateAfter, got {run.state_after!r}"
    )


async def test_run_js_state_after_none_when_missing():
    """When the bridge omits ``stateAfter``, the field must default to ``None``."""
    client = BotClient()
    bridge_response = {
        "ok": True,
        "result": "ack",
        "error": None,
        "durationMs": 7,
        # no stateAfter
    }
    with _stub_call(client, bridge_response):
        run = await client.run_js("bot.chat('ping')", timeout_ms=5_000)

    assert run.state_after is None, (
        f"missing stateAfter must yield None, got {run.state_after!r}"
    )


async def test_run_js_state_after_preserved_on_failure():
    """Even when ``ok=False``, any provided stateAfter must round-trip."""
    client = BotClient()
    bridge_state = {"inventory": {"oak_log": 0}}
    bridge_response = {
        "ok": False,
        "result": None,
        "error": {"message": "no tree found"},
        "durationMs": 200,
        "stateAfter": bridge_state,
    }
    with _stub_call(client, bridge_response):
        run = await client.run_js("await bot.collectBlock(...)", timeout_ms=5_000)

    assert run.ok is False
    assert run.state_after == bridge_state
