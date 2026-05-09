"""CriticAgent — judges whether the action agent's attempt succeeded."""

from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import BaseModel

from llm_client import LLMClient, default_client
from voyager_agents.prompts import critic_messages

LOG = logging.getLogger("omniplay.critic")

Verdict = Literal["success", "incomplete", "failed"]


class CriticVerdict(BaseModel):
    verdict: Verdict
    confidence: float
    feedback: str


class CriticAgent:
    def __init__(self, *, llm: LLMClient | None = None) -> None:
        self.llm = llm or default_client()

    def judge(
        self,
        *,
        task: str,
        code: str,
        runtime_ok: bool,
        runtime_error: str | None,
        runtime_result: str | None,
        snapshot_before: dict[str, Any],
        snapshot_after: dict[str, Any],
    ) -> CriticVerdict:
        messages = critic_messages(
            task=task,
            code=code,
            runtime_ok=runtime_ok,
            runtime_error=runtime_error,
            runtime_result=runtime_result,
            inventory_before=snapshot_before.get("inventory", {}),
            inventory_after=snapshot_after.get("inventory", {}),
            nearby_blocks_before=snapshot_before.get("nearbyBlocks", snapshot_before.get("nearby_blocks", [])),
            nearby_blocks_after=snapshot_after.get("nearbyBlocks", snapshot_after.get("nearby_blocks", [])),
            position_before=snapshot_before.get("position"),
            position_after=snapshot_after.get("position"),
        )
        response = self.llm.complete(messages, schema=CriticVerdict, reasoning_effort="medium")
        verdict = response.parsed
        if not isinstance(verdict, CriticVerdict):
            raise RuntimeError("critic agent did not return a CriticVerdict")
        LOG.info("critic verdict: %s (%.2f) — %s", verdict.verdict, verdict.confidence, verdict.feedback[:120])
        return verdict


__all__ = ["CriticAgent", "CriticVerdict"]
