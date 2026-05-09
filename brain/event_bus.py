"""Agent Event stream scaffold."""

from models import AgentEvent


class EventBus:
    """Broadcasts Agent Events to dashboard subscribers."""

    async def publish(self, event: AgentEvent) -> None:
        """TODO(Person B): broadcast over WS and persist via MemoryStore."""
        raise NotImplementedError("EventBus.publish is scaffold-only")
