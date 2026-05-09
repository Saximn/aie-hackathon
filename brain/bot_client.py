"""HTTP client boundary for the OmniForge runtime."""

from typing import Any

from models import ExecutionResult, PrimitiveAction


class BotClient:
    """Thin adapter around the runtime HTTP API."""

    def __init__(self, base_url: str = "http://localhost:3001") -> None:
        self.base_url = base_url

    async def health(self) -> dict[str, Any]:
        raise NotImplementedError("BotClient.health is scaffold-only")

    async def state(self) -> dict[str, Any]:
        raise NotImplementedError("BotClient.state is scaffold-only")

    async def screenshot_b64(self) -> str | None:
        raise NotImplementedError("BotClient.screenshot_b64 is scaffold-only")

    async def actions(self) -> list[dict[str, Any]]:
        raise NotImplementedError("BotClient.actions is scaffold-only")

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        raise NotImplementedError("BotClient.execute is scaffold-only")
