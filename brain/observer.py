"""Observer — turns the Mineflayer symbolic state into a WorldSnapshot.

The OmniForge VLM screenshot path is dropped for OmniPlay-MC; symbolic state
from the bridge is sufficient. Visual fields are left at their `unknown`
defaults so downstream code (and the dashboard) stays compatible.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from bot_client import BotClient
from models import (
    DerivedRisks,
    Position,
    SymbolicObservation,
    VisualObservation,
    WorldSnapshot,
)

LOG = logging.getLogger("omniplay.observer")

NIGHT_TICKS = (13_000, 23_000)
LOW_HEALTH = 8.0
LOW_HUNGER = 6.0


def _derive_risks(symbolic: SymbolicObservation, time_of_day: int | None) -> DerivedRisks:
    night = "unknown"
    if time_of_day is not None:
        night = "high" if NIGHT_TICKS[0] <= time_of_day <= NIGHT_TICKS[1] else "low"

    hostile = {"zombie", "skeleton", "creeper", "spider", "enderman", "witch"}
    combat = "high" if any(e in hostile for e in symbolic.nearby_entities) else "low"

    food = "unknown"
    if symbolic.hunger is not None:
        food = "high" if symbolic.hunger <= LOW_HUNGER else "low"

    return DerivedRisks(night_risk=night, combat_risk=combat, food_risk=food)


def _normalize_state(raw_state: dict[str, Any]) -> SymbolicObservation:
    pos = raw_state.get("position") or {}
    position = None
    if pos and "x" in pos and "y" in pos and "z" in pos:
        position = Position(x=float(pos["x"]), y=float(pos["y"]), z=float(pos["z"]))
    return SymbolicObservation(
        health=raw_state.get("health"),
        hunger=raw_state.get("hunger"),
        inventory=raw_state.get("inventory") or {},
        nearby_blocks=list(raw_state.get("nearbyBlocks") or raw_state.get("nearby_blocks") or []),
        nearby_entities=list(raw_state.get("nearbyEntities") or raw_state.get("nearby_entities") or []),
        position=position,
        biome=raw_state.get("biome"),
        raw_state=raw_state.get("rawState") or raw_state.get("raw_state") or {},
    )


class Observer:
    """Pull current world state from the Mineflayer bridge."""

    def __init__(self, *, client: BotClient) -> None:
        self.client = client

    async def observe(self, *, cycle: int, goal: str, game: str = "minecraft") -> WorldSnapshot:
        payload = await self.client.get_state()
        raw_state = payload.get("state") or payload
        symbolic = _normalize_state(raw_state if isinstance(raw_state, dict) else {})
        time_of_day_raw = (symbolic.raw_state or {}).get("timeOfDay")
        time_of_day = int(time_of_day_raw) if isinstance(time_of_day_raw, (int, float)) else None
        derived = _derive_risks(symbolic, time_of_day)

        snapshot = WorldSnapshot(
            snapshot_id=uuid.uuid4().hex,
            cycle=cycle,
            game=game,
            goal=goal,
            visual=VisualObservation(),
            symbolic=symbolic,
            derived_risks=derived,
            screenshot_b64=None,
        )
        LOG.debug(
            "observed cycle=%d health=%s hunger=%s inv=%d blocks=%d",
            cycle,
            symbolic.health,
            symbolic.hunger,
            len(symbolic.inventory),
            len(symbolic.nearby_blocks),
        )
        return snapshot


__all__ = ["Observer"]
