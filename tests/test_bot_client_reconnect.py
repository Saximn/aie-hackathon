"""BotClient auto-reconnect behaviour.

When run_js receives "mineflayer not connected", BotClient must:
 1. Re-send a connect call with the stored params.
 2. Retry run_js once.
 3. Return the successful result.
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio  # noqa: F401 — registers asyncio mode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))

from bot_client import BotClient, BridgeError

# Use asyncio-mode=auto (set in pytest.ini / inline marker)
pytestmark = pytest.mark.asyncio


def _not_connected_error():
    return BridgeError("bridge call runJs failed: mineflayer not connected; call connect first")


def _mock_client_with_stored_params() -> BotClient:
    """Return a BotClient that has already 'connected' so _last_connect_params is stored."""
    client = BotClient()
    client._last_connect_params: dict = {
        "host": "localhost", "port": 25565,
        "username": "Voyager", "version": "1.20.4",
    }
    # Pretend process is started so call() guard passes
    client._proc = object()  # type: ignore[assignment]
    return client


async def test_run_js_reconnects_and_retries_on_not_connected():
    """run_js must reconnect once and retry when bridge says 'mineflayer not connected'."""
    client = _mock_client_with_stored_params()
    call_count = 0

    async def fake_call(method, params=None, *, timeout=120.0):
        nonlocal call_count
        call_count += 1
        if method == "connect":
            return {"connected": True}
        if method == "runJs":
            if call_count == 1:  # first runJs attempt
                raise _not_connected_error()
            # second runJs attempt (after reconnect) succeeds
            return {"ok": True, "result": "4 logs", "error": None, "durationMs": 500, "stateAfter": None}
        raise AssertionError(f"unexpected call: {method}")

    with patch.object(client, "call", side_effect=fake_call):
        result = await client.run_js("bot.chat('hi')", timeout_ms=5000)

    assert result.ok, f"expected ok result, got: {result}"
    assert call_count == 3, f"expected 3 calls (runJs, connect, runJs), got {call_count}"


async def test_run_js_raises_if_reconnect_does_not_fix_connection():
    """If the retry also gets 'not connected', BridgeError must propagate (no infinite loop)."""
    client = _mock_client_with_stored_params()

    async def fake_call(method, params=None, *, timeout=120.0):
        if method == "connect":
            return {"connected": True}
        if method == "runJs":
            raise _not_connected_error()
        raise AssertionError(f"unexpected call: {method}")

    with patch.object(client, "call", side_effect=fake_call):
        with pytest.raises(BridgeError, match="mineflayer not connected"):
            await client.run_js("bot.chat('hi')", timeout_ms=5000)


async def test_run_js_raises_immediately_if_no_stored_params():
    """If connect was never called (no stored params), BridgeError propagates without reconnect."""
    client = BotClient()
    client._proc = object()  # type: ignore[assignment]

    async def fake_call(method, params=None, *, timeout=120.0):
        if method == "runJs":
            raise _not_connected_error()
        raise AssertionError(f"unexpected: {method}")

    with patch.object(client, "call", side_effect=fake_call):
        with pytest.raises(BridgeError, match="mineflayer not connected"):
            await client.run_js("bot.chat('hi')", timeout_ms=5000)
