"""GPT-5.5 planning scaffold."""

from models import GameProfile, Plan, WorldSnapshot


class Planner:
    """Produces grounded Plans from profiles, snapshots, memory, and skills."""

    async def plan(
        self,
        goal: str,
        profile: GameProfile,
        snapshot: WorldSnapshot,
        memory_context: str,
        user_constraints: list[str] | None = None,
    ) -> Plan:
        """Create a grounded plan.

        TODO(Person B): call GPT-5.5 through the OpenAI Responses API using
        Structured Outputs. Planner output must be a Plan containing only
        grounded PrimitiveActions.
        """
        raise NotImplementedError("Planner.plan is scaffold-only")
