from __future__ import annotations

import sys
from asyncio import run
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import VisualObservation
from observer import Observer


class FakeBotClient:
    async def screenshot_b64(self) -> str:
        return "base64-png"

    async def state(self) -> dict:
        return {
            "health": 18,
            "hunger": 5,
            "inventory": {"wood": 3, "stone": "bad"},
            "nearby_blocks": ["tree", "dirt"],
            "nearby_entities": ["zombie"],
            "position": {"x": 1, "y": 64, "z": 2},
            "biome": "forest",
            "raw_state": {"adapter": "demo"},
        }


class FakeVision:
    async def observe(self, screenshot_b64: str | None, goal: str, game: str) -> VisualObservation:
        assert screenshot_b64 == "base64-png"
        assert goal == "survive_first_night"
        assert game == "minecraft"
        return VisualObservation(
            scene_summary="A tree is visible near hostile mobs at night.",
            visible_objects=["tree", "zombie"],
            risk_level="medium",
            time_of_day="night",
            ui_state="gameplay",
            confidence=0.8,
        )


def test_observer_builds_world_snapshot_from_visual_and_symbolic_state() -> None:
    snapshot = run(Observer(bot_client=FakeBotClient(), vision=FakeVision()).observe(2, "survive_first_night", "minecraft"))

    assert snapshot.snapshot_id == "minecraft:2"
    assert snapshot.screenshot_b64 == "base64-png"
    assert snapshot.visual.visible_objects == ["tree", "zombie"]
    assert snapshot.symbolic.inventory == {"wood": 3}
    assert snapshot.symbolic.nearby_entities == ["zombie"]
    assert snapshot.symbolic.position is not None
    assert snapshot.symbolic.position.y == 64
    assert snapshot.derived_risks.night_risk == "high"
    assert snapshot.derived_risks.combat_risk == "high"
    assert snapshot.derived_risks.food_risk == "high"
