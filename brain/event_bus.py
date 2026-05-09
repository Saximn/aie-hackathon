"""Agent Event stream scaffold."""

from models import AgentEvent


class EventBus:
    """Broadcasts Agent Events to dashboard subscribers."""

    def __init__(self) -> None:
        self._events: list[AgentEvent] = []

    @property
    def events(self) -> tuple[AgentEvent, ...]:
        """Return published events for tests and local status endpoints."""
        return tuple(self._events)

    async def publish(self, event: AgentEvent) -> None:
        """Publish an Agent Event.

        The scaffold keeps an in-memory event stream. A later dashboard adapter
        can subscribe here without changing AgentLoop callers.
        """
        self._events.append(event)
