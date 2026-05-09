"""GPT-5.5 planning scaffold."""

from models import Plan, WorldSnapshot


class Planner:
    """Produces grounded Plans from snapshots, memory, and skills."""

    async def plan(self, goal: str, snapshot: WorldSnapshot, memory_context: str) -> Plan:
        # TODO(Person B): call OpenAI Responses API with Structured Outputs.
        return Plan(goal=goal, snapshot_id=snapshot.snapshot_id)
