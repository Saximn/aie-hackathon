"""Memory store scaffold."""

from models import AgentEvent, Skill


class MemoryStore:
    """Persists events, failures, user preferences, and structured Skills."""

    async def append_event(self, event: AgentEvent) -> None:
        """TODO(Person B): write to Convex or local JSON fallback."""
        raise NotImplementedError("MemoryStore.append_event is scaffold-only")

    async def upsert_skill(self, skill: Skill) -> None:
        """TODO(Person B): persist Skill metadata and verification status."""
        raise NotImplementedError("MemoryStore.upsert_skill is scaffold-only")

    async def context(self) -> str:
        """TODO(Person B): summarize relevant memories for the Planner."""
        raise NotImplementedError("MemoryStore.context is scaffold-only")
