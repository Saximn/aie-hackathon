"""Primitive Action execution scaffold."""

from bot_client import BotClient
from models import ExecutionResult, PrimitiveAction


class Executor:
    """Dispatches validated PrimitiveActions to the runtime."""

    def __init__(self, bot_client: BotClient | None = None) -> None:
        self._bot_client = bot_client or BotClient()

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        """Run a PrimitiveAction without reasoning at execution time."""
        return await self._bot_client.execute(action)
