"""ActionAgent — generates an async JS body to attempt one task."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from llm_client import LLMClient, default_client
from voyager_agents.prompts import action_messages

LOG = logging.getLogger("omniplay.action")


class ActionResult(BaseModel):
    explain: str
    plan: list[str] = Field(default_factory=list)
    code: str
    name: str = "unnamed_skill"


def snapshot_to_text(snapshot: dict[str, Any]) -> str:
    """Render a Mineflayer SymbolicObservation dict into a compact prompt block."""
    pos = snapshot.get("position") or {}
    return (
        f"position: ({pos.get('x', '?')}, {pos.get('y', '?')}, {pos.get('z', '?')})\n"
        f"biome: {snapshot.get('biome')}\n"
        f"health: {snapshot.get('health')}  hunger: {snapshot.get('hunger')}\n"
        f"inventory: {snapshot.get('inventory', {})}\n"
        f"nearby_blocks: {snapshot.get('nearbyBlocks', snapshot.get('nearby_blocks', []))[:25]}\n"
        f"nearby_entities: {snapshot.get('nearbyEntities', snapshot.get('nearby_entities', []))[:10]}\n"
        f"time_of_day: {(snapshot.get('rawState') or {}).get('timeOfDay', 'unknown')}\n"
    )


class ActionAgent:
    def __init__(self, *, llm: LLMClient | None = None) -> None:
        self.llm = llm or default_client()

    def generate_code(
        self,
        *,
        task: str,
        rationale: str,
        snapshot: dict[str, Any],
        retrieved_skills: list[dict[str, str]],
        last_error: str | None = None,
        last_code: str | None = None,
    ) -> ActionResult:
        messages = action_messages(
            task=task,
            rationale=rationale,
            snapshot_text=snapshot_to_text(snapshot),
            retrieved_skills=retrieved_skills,
            last_error=last_error,
            last_code=last_code,
        )
        response = self.llm.complete(messages, schema=ActionResult, reasoning_effort="high")
        result = response.parsed
        if not isinstance(result, ActionResult):
            raise RuntimeError("action agent did not return an ActionResult")
        if not result.code.strip():
            raise RuntimeError("action agent returned empty code")
        LOG.info("action agent emitted %d chars of code for task: %s", len(result.code), task)
        return result


__all__ = ["ActionAgent", "ActionResult", "snapshot_to_text"]
