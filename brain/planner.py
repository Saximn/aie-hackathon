"""Planner — thin wrapper around `voyager_agents.action.ActionAgent`.

Voyager-Plus generates JS code as the executable plan, but we still emit a
`Plan` model for the dashboard so judges can see the agent's structured
reasoning trace (explanation + ordered steps + the JS body).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from models import JsCodeAction, Plan, WorldSnapshot
from voyager_agents import ActionAgent, ActionResult, RetrievedSkill

LOG = logging.getLogger("omniplay.planner")


class Planner:
    def __init__(self, *, action_agent: ActionAgent | None = None) -> None:
        self.action_agent = action_agent or ActionAgent()

    def plan(
        self,
        *,
        task: str,
        rationale: str,
        snapshot: WorldSnapshot,
        retrieved_skills: list[RetrievedSkill],
        last_error: str | None = None,
        last_code: str | None = None,
    ) -> tuple[Plan, ActionResult, JsCodeAction]:
        snapshot_dict = _snapshot_for_prompt(snapshot)
        result = self.action_agent.generate_code(
            task=task,
            rationale=rationale,
            snapshot=snapshot_dict,
            retrieved_skills=[s.as_prompt_dict() for s in retrieved_skills],
            last_error=last_error,
            last_code=last_code,
        )
        action = JsCodeAction(
            id=uuid.uuid4().hex,
            name=result.name or "unnamed_skill",
            description=result.explain,
            code=result.code,
            expected_outcome=task,
        )
        plan = Plan(
            plan_id=uuid.uuid4().hex,
            goal=task,
            snapshot_id=snapshot.snapshot_id,
            used_skills=[s.record.name for s in retrieved_skills],
            actions=[],
        )
        return plan, result, action


def _snapshot_for_prompt(snapshot: WorldSnapshot) -> dict[str, Any]:
    sym = snapshot.symbolic
    return {
        "position": sym.position.model_dump() if sym.position else None,
        "biome": sym.biome,
        "health": sym.health,
        "hunger": sym.hunger,
        "inventory": sym.inventory,
        "nearbyBlocks": sym.nearby_blocks,
        "nearbyEntities": sym.nearby_entities,
        "rawState": sym.raw_state,
    }


__all__ = ["Planner"]
