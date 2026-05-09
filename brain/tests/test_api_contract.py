from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot_client import BotClient
from main import app
from models import RuntimeActions, RuntimeHealth, RuntimeScreenshot, RuntimeState


class FakeBotClient(BotClient):
    def __init__(self, payloads: dict[str, dict]) -> None:
        self.payloads = payloads
        super().__init__(base_url="http://runtime.test")

    async def _get_json(self, path: str) -> dict:
        return self.payloads[path]


def test_brain_lifecycle_contract_exposes_stable_status() -> None:
    client = TestClient(app)

    health = client.get("/health").json()
    assert health["brain"] == "ready"
    assert "runtime" in health
    assert health["features"]["game_profiles"] is True

    started = client.post(
        "/start",
        json={
            "game": "minecraft",
            "goal": "survive_first_night",
            "user_constraints": ["avoid fast combat"],
            "max_cycles": 1,
            "research_allowed": False,
        },
    ).json()

    assert started["accepted"] is True
    assert started["status"]["running"] is True
    assert started["status"]["game"] == "minecraft"
    assert started["status"]["tracks"]["research"] == "unavailable"

    status = client.get("/status").json()
    assert status["goal"] == "survive_first_night"

    stopped = client.post("/stop").json()
    assert stopped["stopped"] is True
    assert stopped["status"]["running"] is False


def test_runtime_contract_models_use_snake_case_json() -> None:
    health = RuntimeHealth(
        runtime="ready",
        adapters=["generic_input"],
        screenshot_available=False,
        symbolic_state_available=True,
        version="0.1.0",
    )
    state = RuntimeState(available=True, game="minecraft")
    screenshot = RuntimeScreenshot(screenshot_b64=None, media_type="image/png")
    actions = RuntimeActions(
        actions=[
            {
                "type": "wait",
                "adapter": "generic_input",
                "description": "Wait for a duration.",
                "required_args": ["duration_ms"],
            }
        ]
    )

    assert "screenshot_available" in health.model_dump()
    assert "symbolic" in state.model_dump()
    assert "screenshot_b64" in screenshot.model_dump()
    assert actions.actions[0].required_args == ["duration_ms"]


def test_bot_client_accepts_legacy_camel_case_runtime_payloads() -> None:
    import asyncio

    client = FakeBotClient(
        {
            "/health": {
                "runtime": "ready",
                "adapters": ["generic_input"],
                "screenshotAvailable": True,
                "symbolicStateAvailable": False,
                "version": "0.1.0",
            },
            "/screenshot": {
                "screenshotB64": "abc123",
                "mediaType": "image/png",
            },
            "/actions": {
                "actions": [
                    {
                        "type": "wait",
                        "adapter": "generic_input",
                        "description": "Wait.",
                        "requiredArgs": ["duration_ms"],
                    }
                ]
            },
        }
    )

    assert asyncio.run(client.health())["screenshot_available"] is True
    assert asyncio.run(client.screenshot_b64()) == "abc123"
    assert asyncio.run(client.actions())[0]["required_args"] == ["duration_ms"]
