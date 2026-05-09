"""Async Agent Event broadcast for OmniPlay-MC.

Subscribers (FastAPI WS handlers, the narrator hook, the Convex mirror) attach
asyncio queues; publishers fan-out to all of them. Local-only — Convex
persistence is a separate sink wired in `observability_hook.py`.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from models import AgentEvent

LOG = logging.getLogger("omniplay.event_bus")


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[AgentEvent]] = set()
        self._lock = asyncio.Lock()
        self._recent: list[AgentEvent] = []
        self._max_recent = 256

    async def publish(self, event: AgentEvent) -> None:
        self._recent.append(event)
        if len(self._recent) > self._max_recent:
            self._recent = self._recent[-self._max_recent :]
        async with self._lock:
            subscribers = list(self._subscribers)
        for queue in subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                LOG.warning("event subscriber queue full; dropping event %s", event.event_type)

    def recent(self, limit: int = 50) -> list[AgentEvent]:
        return list(self._recent[-limit:])

    @asynccontextmanager
    async def subscribe(self, *, max_size: int = 128) -> AsyncIterator[asyncio.Queue[AgentEvent]]:
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=max_size)
        async with self._lock:
            self._subscribers.add(queue)
        try:
            yield queue
        finally:
            async with self._lock:
                self._subscribers.discard(queue)


_DEFAULT_BUS: EventBus | None = None


def default_bus() -> EventBus:
    global _DEFAULT_BUS
    if _DEFAULT_BUS is None:
        _DEFAULT_BUS = EventBus()
    return _DEFAULT_BUS


__all__ = ["EventBus", "default_bus"]
