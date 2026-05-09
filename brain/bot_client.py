"""HTTP client for the OmniForge runtime."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from models import ExecutionResult, PrimitiveAction


class BotClient:
    """Thin adapter around the runtime HTTP API."""

    def __init__(self, base_url: str = "http://localhost:3001") -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def health(self) -> dict[str, Any]:
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    async def state(self) -> dict[str, Any]:
        response = await self.client.get(f"{self.base_url}/state")
        response.raise_for_status()
        return response.json()

    async def screenshot_b64(self) -> str | None:
        response = await self.client.get(f"{self.base_url}/screenshot")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return base64.b64encode(response.content).decode("ascii")

    async def actions(self) -> list[dict[str, Any]]:
        response = await self.client.get(f"{self.base_url}/actions")
        response.raise_for_status()
        return response.json()

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        response = await self.client.post(f"{self.base_url}/action", json=action.model_dump(mode="json"))
        response.raise_for_status()
        payload = response.json()
        return ExecutionResult(
            action_id=payload.get("action_id") or payload.get("actionId") or action.id,
            success=payload.get("success", False),
            result=payload.get("result", ""),
            evidence=payload.get("evidence", {}),
        )

    async def close(self) -> None:
        await self.client.aclose()
