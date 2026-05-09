"""Executor scaffold for dispatching PrimitiveActions to the runtime."""

from bot_client import BotClient
from models import ExecutionResult, PrimitiveAction


class Executor:
    """Executes validated PrimitiveActions via BotClient."""

    def __init__(self, bot_client: BotClient) -> None:
        self.bot_client = bot_client

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        """Run a PrimitiveAction without adding reasoning at execution time."""
        return await self.bot_client.execute(action)
