"""MemoryStore scaffold."""

from models import DashboardEvent, Skill


class MemoryStore:
    """Persists episodes, facts, failures, preferences, and skills."""

    async def append_event(self, event: DashboardEvent) -> None:
        # TODO(Person B): write to Convex when enabled, otherwise JSON fallback.
        _ = event

    async def upsert_skill(self, skill: Skill) -> None:
        # TODO(Person B): persist Skill with confidence and verification metadata.
        _ = skill

    async def context(self) -> str:
        # TODO(Person B): summarize recent memory for Planner.
        return ""
