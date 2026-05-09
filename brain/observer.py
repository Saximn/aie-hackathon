"""World observation."""

from __future__ import annotations

from typing import Any, Protocol

from bot_client import BotClient
from models import DerivedRisks, SymbolicObservation, VisualObservation, WorldSnapshot


class VisionAdapter(Protocol):
    """Adapter seam for VLM-derived Visual Observation."""

    async def observe(self, screenshot_b64: str | None, goal: str, game: str) -> VisualObservation:
        """Return a structured Visual Observation."""


class Observer:
    """Turns screenshot and optional symbolic runtime state into a WorldSnapshot."""

    def __init__(self, bot_client: BotClient | None = None, vision: VisionAdapter | None = None) -> None:
        self._bot_client = bot_client or BotClient()
        self._vision = vision or NoopVisionAdapter()

    async def observe(self, cycle: int, goal: str, game: str) -> WorldSnapshot:
        """Collect a WorldSnapshot from runtime observation seams."""
        screenshot_b64 = await self._bot_client.screenshot_b64()
        state = await self._bot_client.state()
        visual = await self._vision.observe(screenshot_b64, goal, game)
        symbolic = _symbolic_observation_from_state(state)

        return WorldSnapshot(
            snapshot_id=f"{game}:{cycle}",
            cycle=cycle,
            game=game,
            goal=goal,
            visual=visual,
            symbolic=symbolic,
            derived_risks=_derive_risks(visual, symbolic),
            screenshot_b64=screenshot_b64,
        )


class NoopVisionAdapter:
    """Default adapter used until a VLM-backed implementation is configured."""

    async def observe(self, screenshot_b64: str | None, goal: str, game: str) -> VisualObservation:
        confidence = 0.1 if screenshot_b64 else 0.0
        return VisualObservation(
            scene_summary=f"No VLM adapter configured for {game}.",
            visible_objects=[],
            risk_level="unknown",
            time_of_day="unknown",
            ui_state="unknown",
            confidence=confidence,
        )


def _symbolic_observation_from_state(state: dict[str, Any]) -> SymbolicObservation:
    position = state.get("position")
    return SymbolicObservation(
        health=_optional_number(state.get("health")),
        hunger=_optional_number(state.get("hunger")),
        inventory=_string_int_map(state.get("inventory")),
        nearby_blocks=_string_list(state.get("nearby_blocks") or state.get("nearbyBlocks")),
        nearby_entities=_string_list(state.get("nearby_entities") or state.get("nearbyEntities")),
        position=position if isinstance(position, dict) else None,
        biome=str(state["biome"]) if state.get("biome") is not None else None,
        raw_state=state.get("raw_state") or state.get("rawState") or {},
    )


def _derive_risks(visual: VisualObservation, symbolic: SymbolicObservation) -> DerivedRisks:
    night_risk = "high" if visual.time_of_day == "night" else "low" if visual.time_of_day == "day" else "unknown"
    combat_risk = "high" if visual.risk_level == "high" or symbolic.nearby_entities else visual.risk_level
    food_risk = "unknown"
    if symbolic.hunger is not None:
        food_risk = "high" if symbolic.hunger <= 6 else "medium" if symbolic.hunger <= 12 else "low"

    return DerivedRisks(
        night_risk=night_risk,
        combat_risk=combat_risk,
        food_risk=food_risk,
    )


def _optional_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _string_int_map(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, amount in value.items():
        if isinstance(amount, int) and not isinstance(amount, bool):
            result[str(key)] = amount
    return result


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]
