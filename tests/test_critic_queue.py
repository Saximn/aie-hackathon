"""Slice 7 (TDD): background queue for LLM critic calls.

After a successful action, the next observe→plan cycle does not need to wait
for the critic — it only needs the verdict by episode end (for skill
promotion).  ``CriticQueue.submit`` schedules the critic as a background task
and returns immediately.

RED:  module does not exist yet.
GREEN: ``submit`` is non-blocking, the verdict callback fires once the
       critic future resolves, and ``drain`` awaits all pending tasks.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# submit is non-blocking
# ---------------------------------------------------------------------------

async def test_submit_does_not_block():
    """submit() must return without awaiting the critic coroutine."""
    from critic_queue import CriticQueue

    q = CriticQueue()

    async def slow_critic() -> dict:
        await asyncio.sleep(0.2)
        return {"verdict": "success"}

    received: list[dict] = []

    def on_verdict(verdict: dict) -> None:
        received.append(verdict)

    t0 = time.perf_counter()
    q.submit(slow_critic(), on_verdict)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.05, (
        f"submit() should return immediately, took {elapsed*1000:.0f}ms"
    )

    assert q.pending_count == 1
    assert received == []  # callback hasn't fired yet

    await q.drain()
    assert received == [{"verdict": "success"}]


# ---------------------------------------------------------------------------
# Callback is invoked with the verdict
# ---------------------------------------------------------------------------

async def test_callback_invoked_with_verdict():
    from critic_queue import CriticQueue

    q = CriticQueue()
    received: list[dict] = []

    async def critic() -> dict:
        return {"verdict": "incomplete", "feedback": "still 1 short"}

    q.submit(critic(), received.append)
    await q.drain()

    assert received == [{"verdict": "incomplete", "feedback": "still 1 short"}]


# ---------------------------------------------------------------------------
# drain waits for all pending tasks
# ---------------------------------------------------------------------------

async def test_drain_waits_for_all():
    from critic_queue import CriticQueue

    q = CriticQueue()
    completed: list[int] = []

    async def make_critic(idx: int, delay: float):
        await asyncio.sleep(delay)
        return idx

    q.submit(make_critic(1, 0.05), completed.append)
    q.submit(make_critic(2, 0.10), completed.append)
    q.submit(make_critic(3, 0.02), completed.append)

    assert q.pending_count == 3
    await q.drain()

    assert sorted(completed) == [1, 2, 3]
    assert q.pending_count == 0


async def test_drain_with_no_pending_tasks_is_noop():
    from critic_queue import CriticQueue

    q = CriticQueue()
    await q.drain()  # must not raise


# ---------------------------------------------------------------------------
# Errors in the critic must not crash the loop
# ---------------------------------------------------------------------------

async def test_critic_exception_is_swallowed_with_callback_signal():
    """If the critic raises, drain() must still complete and callback signal it."""
    from critic_queue import CriticQueue

    q = CriticQueue()
    received: list = []

    async def boom() -> dict:
        raise RuntimeError("openai went boom")

    def on_verdict(verdict_or_error) -> None:
        received.append(verdict_or_error)

    q.submit(boom(), on_verdict)
    await q.drain()  # must not raise

    assert q.pending_count == 0
    assert len(received) == 1
    # Either the exception itself or a sentinel — verifier only requires
    # the callback fires once with something distinguishable.
    assert isinstance(received[0], Exception) or "error" in str(received[0]).lower()


# ---------------------------------------------------------------------------
# Callback exceptions must not break drain
# ---------------------------------------------------------------------------

async def test_callback_exception_is_swallowed():
    from critic_queue import CriticQueue

    q = CriticQueue()

    async def critic():
        return {"verdict": "success"}

    def bad_callback(_v):
        raise ValueError("bad callback")

    q.submit(critic(), bad_callback)
    await q.drain()  # must not raise

    assert q.pending_count == 0
