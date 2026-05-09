"""Observer scaffold for building WorldSnapshot objects."""

from models import WorldSnapshot


class Observer:
    """Turns bot state and optional screenshot bytes into a WorldSnapshot."""

    async def observe(self, cycle: int) -> WorldSnapshot:
        # TODO(Person B): fetch /state and /screenshot through BotClient.
        return WorldSnapshot(snapshot_id=f"cycle-{cycle}", cycle=cycle)
