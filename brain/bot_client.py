"""HTTP client boundary for the OmniForge runtime."""

from __future__ import annotations

from typing import Any

import httpx

from models import (
    ExecutionResult,
    PrimitiveAction,
    RuntimeActions,
    RuntimeHealth,
    RuntimeScreenshot,
    RuntimeState,
    SymbolicObservation,
)


class BotClient:
    """Adapter around the Runtime HTTP contract."""

    def __init__(self, base_url: str = "http://localhost:3001") -> None:
        self.base_url = base_url.rstrip("/")

    async def health(self) -> dict[str, Any]:
        return RuntimeHealth(**_snake_keys(await self._get_json("/health"))).model_dump()

    async def state(self) -> dict[str, Any]:
        data = _snake_keys(await self._get_json("/state"))
        if "symbolic" in data:
            return RuntimeState(**data).symbolic.model_dump()
        return SymbolicObservation(**data).model_dump()

    async def screenshot_b64(self) -> str | None:
        screenshot = RuntimeScreenshot(**_snake_keys(await self._get_json("/screenshot")))
        return screenshot.screenshot_b64

    async def actions(self) -> list[dict[str, Any]]:
        response = await self._get_json("/actions")
        data = {"actions": response} if isinstance(response, list) else _snake_keys(response)
        return [action.model_dump() for action in RuntimeActions(**data).actions]

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post("/action", json=_action_payload(action))
            response.raise_for_status()
            data = response.json()

        return ExecutionResult(
            action_id=str(data.get("actionId") or data.get("action_id") or action.id),
            success=bool(data.get("success")),
            result=str(data.get("result", "")),
            evidence=data.get("evidence") if isinstance(data.get("evidence"), dict) else {},
        )

    async def _get_json(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(path)
            response.raise_for_status()
            data = response.json()
        return data if isinstance(data, dict) else {}


def _action_payload(action: PrimitiveAction) -> dict[str, Any]:
    return {
        "id": action.id,
        "type": str(action.type),
        "args": action.args,
        "expected_result": action.expected_result,
        "timeout_ms": action.timeout_ms,
        "adapter": str(action.adapter),
    }


def _snake_keys(data: Any) -> Any:
    aliases = {
        "screenshotB64": "screenshot_b64",
        "mediaType": "media_type",
        "capturedAt": "captured_at",
        "screenshotAvailable": "screenshot_available",
        "symbolicStateAvailable": "symbolic_state_available",
        "requiredArgs": "required_args",
    }
    if isinstance(data, list):
        return [_snake_keys(item) for item in data]
    if isinstance(data, dict):
        return {aliases.get(key, key): _snake_keys(value) for key, value in data.items()}
    return data
