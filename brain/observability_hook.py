"""Single seam for emitting Agent Events to the event bus + memory store.

Every agent module calls `Observability.emit(...)` rather than reaching into
the event bus or memory store directly. That keeps the dashboard mirror,
narrator triggers, and any future sinks (e.g. cost tracking) routed through
one place.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from event_bus import EventBus, default_bus
from memory_store import MemoryStore
from models import AgentEvent, AgentEventType

LOG = logging.getLogger("omniplay.observability")

EventListener = Callable[[AgentEvent], Awaitable[None]]


class Observability:
    """Façade over the event bus, the memory store, and any custom listeners."""

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        memory: MemoryStore | None = None,
    ) -> None:
        self.event_bus = event_bus or default_bus()
        self.memory = memory
        self._listeners: list[EventListener] = []

    def add_listener(self, listener: EventListener) -> None:
        self._listeners.append(listener)

    async def emit(
        self,
        event_type: AgentEventType,
        data: dict[str, Any],
        *,
        cycle: int = 0,
        snapshot_id: str | None = None,
    ) -> AgentEvent:
        event = AgentEvent(
            id=uuid.uuid4().hex,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            cycle=cycle,
            snapshot_id=snapshot_id,
            data=data,
        )
        await self.event_bus.publish(event)
        if self.memory is not None:
            try:
                await self.memory.append_event(event)
            except Exception as exc:
                LOG.warning("memory.append_event failed for %s: %s", event_type, exc)
        for listener in self._listeners:
            try:
                await listener(event)
            except Exception as exc:
                LOG.warning("listener failed for %s: %s", event_type, exc)
        return event


__all__ = ["Observability", "EventListener"]
