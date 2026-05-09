"""World observation scaffold."""

from models import WorldSnapshot


class Observer:
    """Turns screenshot and optional symbolic runtime state into a WorldSnapshot."""

    async def observe(self, cycle: int, goal: str, game: str) -> WorldSnapshot:
        """Collect a WorldSnapshot.

        TODO(Person B): fetch /state and /screenshot, call VLM through the
        OpenAI Responses API with Structured Outputs, and derive risks.
        """
        raise NotImplementedError("Observer.observe is scaffold-only")
