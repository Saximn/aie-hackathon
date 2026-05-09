"""Executor scaffold for dispatching PrimitiveActions to the bot runtime."""

from bot_client import BotClient
from models import ExecutionResult, PrimitiveAction


class Executor:
    """Executes validated PrimitiveActions via BotClient."""

    def __init__(self, bot_client: BotClient) -> None:
        self.bot_client = bot_client

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        # TODO(Person B): add action serialization and event emission hooks.
        return await self.bot_client.execute(action)
