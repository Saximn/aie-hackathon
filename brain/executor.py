"""Primitive Action execution."""

from bot_client import BotClient
from models import ExecutionResult, PrimitiveAction


class Executor:
    """Dispatches validated PrimitiveActions to the runtime."""

    def __init__(self, bot_client: BotClient | None = None) -> None:
        self._bot_client = bot_client or BotClient()

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        """Run a PrimitiveAction without reasoning at execution time."""
        try:
            return await self._bot_client.execute(action)
        except Exception as exc:
            return ExecutionResult(
                action_id=action.id,
                success=False,
                result=f"runtime unavailable: {type(exc).__name__}",
                evidence={"error": str(exc)},
            )
