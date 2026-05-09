"""Observer scaffold for building WorldSnapshot objects."""

from __future__ import annotations

from bot_client import BotClient
from models import DerivedRisks, Position, SymbolicObservation, VisualObservation, WorldSnapshot


class Observer:
    """Turns screenshot and optional symbolic runtime state into a WorldSnapshot."""

    def __init__(self, bot_client: BotClient | None = None) -> None:
        self.bot_client = bot_client

    async def observe(self, cycle: int, goal: str, game: str) -> WorldSnapshot:
        """Collect a single generic OmniForge world snapshot.

        TODO(Person B): send the screenshot to a VLM through the OpenAI
        Responses API with Structured Outputs to fill VisualObservation.
        """
        state: dict = {}
        screenshot_b64: str | None = None
        if self.bot_client is not None:
            state = await self.bot_client.state()
            screenshot_b64 = await self.bot_client.screenshot_b64()

        visual = self._fallback_visual(state)
        symbolic = self._symbolic_from_state(state)
        return WorldSnapshot(
            snapshot_id=f"cycle-{cycle}",
            cycle=cycle,
            game=game,
            goal=goal,
            visual=visual,
            symbolic=symbolic,
            derived_risks=self._derive_risks(visual, symbolic),
            screenshot_b64=screenshot_b64,
        )

    def _fallback_visual(self, state: dict) -> VisualObservation:
        visible_objects = state.get("visibleObjects") or state.get("visible_objects") or []
        return VisualObservation(
            scene_summary=state.get("sceneSummary") or state.get("scene_summary") or "",
            visible_objects=list(visible_objects),
            risk_level=state.get("riskLevel") or state.get("risk_level") or "unknown",
            time_of_day=state.get("timeOfDay") or state.get("time_of_day") or "unknown",
            ui_state=state.get("uiState") or state.get("ui_state") or "unknown",
            confidence=float(state.get("confidence", 0.0)),
        )

    def _symbolic_from_state(self, state: dict) -> SymbolicObservation:
        inventory = state.get("inventory", {})
        if isinstance(inventory, list):
            inventory = {item.get("name", "unknown"): int(item.get("count", 0)) for item in inventory}

        position = state.get("position")
        parsed_position = Position(**position) if isinstance(position, dict) else None

        return SymbolicObservation(
            health=state.get("health"),
            hunger=state.get("hunger") or state.get("food"),
            inventory=inventory if isinstance(inventory, dict) else {},
            nearby_blocks=state.get("nearbyBlocks") or state.get("nearby_blocks") or [],
            nearby_entities=state.get("nearbyEntities") or state.get("nearby_entities") or [],
            position=parsed_position,
            biome=state.get("biome"),
            raw_state=state,
        )

    def _derive_risks(self, visual: VisualObservation, symbolic: SymbolicObservation) -> DerivedRisks:
        night_risk = "high" if visual.time_of_day == "night" else "low" if visual.time_of_day == "day" else "unknown"
        combat_risk = "medium" if symbolic.nearby_entities else visual.risk_level
        food_risk = "medium"
        if symbolic.hunger is not None:
            food_risk = "high" if symbolic.hunger <= 6 else "low" if symbolic.hunger >= 14 else "medium"
        return DerivedRisks(night_risk=night_risk, combat_risk=combat_risk, food_risk=food_risk)
