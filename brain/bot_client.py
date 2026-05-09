"""HTTP client for Person A's Mineflayer Runtime."""

import httpx

from models import ExecutionResult, PrimitiveAction


class BotClient:
    """Thin adapter around the bot HTTP API."""

    def __init__(self, base_url: str = "http://localhost:3001") -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def health(self) -> dict:
        # TODO(Person B): normalize bot health errors.
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        # TODO(Person B): send typed action or serialize if Person A only accepts strings.
        response = await self.client.post(f"{self.base_url}/action", json=action.model_dump(mode="json"))
        response.raise_for_status()
        payload = response.json()
        return ExecutionResult(action_id=action.id, success=payload.get("success", False), result=payload.get("result", ""), evidence=payload.get("evidence", {}))

    async def close(self) -> None:
        await self.client.aclose()
