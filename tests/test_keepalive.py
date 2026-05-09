"""TDD: BotClient.keep_alive() must periodically ping the bridge.

RED: run before adding keep_alive to bot_client.py.
GREEN: pass once keep_alive is implemented.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))

from bot_client import BotClient

pytestmark = pytest.mark.asyncio


async def test_keep_alive_pings_at_interval():
    """keep_alive() must call ping() at least twice within 3 * interval seconds."""
    client = BotClient()
    ping_count = 0

    async def fake_ping():
        nonlocal ping_count
        ping_count += 1
        return {"pong": True}

    with patch.object(client, "ping", side_effect=fake_ping):
        task = asyncio.create_task(client.keep_alive(interval=0.05))
        await asyncio.sleep(0.15)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    assert ping_count >= 2, f"expected >=2 pings in 3*interval, got {ping_count}"


async def test_keep_alive_survives_ping_error():
    """keep_alive() must not raise if ping() throws — just log and keep going."""
    client = BotClient()
    call_count = 0

    async def flaky_ping():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("bridge timeout")
        return {"pong": True}

    with patch.object(client, "ping", side_effect=flaky_ping):
        task = asyncio.create_task(client.keep_alive(interval=0.05))
        await asyncio.sleep(0.15)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Must have attempted at least 2 pings despite first failing
    assert call_count >= 2


async def test_keep_alive_is_cancellable():
    """keep_alive() must honour asyncio.CancelledError cleanly."""
    client = BotClient()

    async def ok_ping():
        return {"pong": True}

    with patch.object(client, "ping", side_effect=ok_ping):
        task = asyncio.create_task(client.keep_alive(interval=1.0))
        await asyncio.sleep(0.01)
        task.cancel()
        # Should not raise anything other than CancelledError
        with pytest.raises(asyncio.CancelledError):
            await task
