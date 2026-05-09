"""Background queue for LLM critic calls.

The Voyager critic verdict is needed for skill promotion at episode end, but
nothing in the next observe → plan → execute cycle depends on it.  Running
the critic in the background lets the loop start the next cycle immediately
(saves the full ~6s critic call from the critical path).

Friend's one-line wiring inside ``agent_loop.py`` after a successful run::

    from critic_queue import default_queue
    default_queue().submit(
        verifier.verify_async(...),     # any awaitable returning the verdict
        on_verdict=lambda v: handle_promote(v),
    )

Then once per episode, before tearing down::

    await default_queue().drain()
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

LOG = logging.getLogger("omniplay.critic_queue")

VerdictCallback = Callable[[Any], None]


class CriticQueue:
    """Track in-flight background critic tasks and await them on demand.

    The class is intentionally minimal — it doesn't enforce concurrency limits
    or maintain a worker pool.  Each :meth:`submit` schedules a fresh
    :class:`asyncio.Task` that runs the supplied awaitable to completion and
    invokes the callback with the result (or an :class:`Exception` if the
    awaitable raised).  Callback exceptions are logged and swallowed so a buggy
    handler never tears down the agent loop.
    """

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[None]] = set()

    @property
    def pending_count(self) -> int:
        """Number of background tasks still in flight."""
        return sum(1 for t in self._tasks if not t.done())

    def submit(
        self,
        awaitable: Awaitable[Any],
        on_verdict: VerdictCallback | None = None,
    ) -> asyncio.Task[None]:
        """Schedule *awaitable* to run in the background.

        Returns the wrapping :class:`asyncio.Task` so callers can cancel it,
        but the typical caller just fires and awaits :meth:`drain` later.
        """
        task = asyncio.create_task(self._run(awaitable, on_verdict))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def drain(self) -> None:
        """Await all in-flight background tasks.

        Safe to call repeatedly; safe to call when no tasks are pending.
        Exceptions in individual tasks have already been swallowed by
        :meth:`_run` so this never raises.
        """
        if not self._tasks:
            return
        pending = [t for t in self._tasks if not t.done()]
        if not pending:
            return
        await asyncio.gather(*pending, return_exceptions=True)

    async def _run(
        self,
        awaitable: Awaitable[Any],
        on_verdict: VerdictCallback | None,
    ) -> None:
        try:
            verdict: Any = await awaitable
        except Exception as exc:
            LOG.warning("background critic raised: %s", exc)
            verdict = exc

        if on_verdict is None:
            return
        try:
            on_verdict(verdict)
        except Exception as exc:
            LOG.warning("critic callback raised: %s", exc)


_DEFAULT: CriticQueue | None = None


def default_queue() -> CriticQueue:
    """Process-wide singleton, lazily constructed."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = CriticQueue()
    return _DEFAULT


__all__ = ["CriticQueue", "default_queue"]
