"""CurriculumAgent — proposes the next task given current world snapshot and history."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from llm_client import LLMClient, default_client
from voyager_agents.prompts import curriculum_messages

LOG = logging.getLogger("omniplay.curriculum")


class CurriculumProposal(BaseModel):
    task: str
    rationale: str
    context: dict[str, str] = Field(default_factory=dict)


class CurriculumAgent:
    def __init__(self, *, llm: LLMClient | None = None) -> None:
        self.llm = llm or default_client()

    def next_task(
        self,
        *,
        biome: str | None,
        time_of_day: str,
        health: float | None,
        hunger: float | None,
        inventory: dict[str, int],
        nearby_blocks: list[str],
        nearby_entities: list[str],
        completed_tasks: list[str],
        failed_tasks: list[str],
        user_constraints: str | None = None,
    ) -> CurriculumProposal:
        messages = curriculum_messages(
            biome=biome,
            time_of_day=time_of_day,
            health=health,
            hunger=hunger,
            inventory=inventory,
            nearby_blocks=nearby_blocks,
            nearby_entities=nearby_entities,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            user_constraints=user_constraints,
        )
        response = self.llm.complete(messages, schema=CurriculumProposal, reasoning_effort="medium")
        proposal = response.parsed
        if not isinstance(proposal, CurriculumProposal):
            raise RuntimeError("curriculum agent did not return a CurriculumProposal")
        LOG.info("curriculum proposed: %s", proposal.task)
        return proposal

    def fixed_task(self, task: str, *, rationale: str = "user-supplied task") -> CurriculumProposal:
        """Bypass the LLM with a hardcoded task (used by `--task` flag and the demo curriculum)."""
        return CurriculumProposal(task=task, rationale=rationale, context={"source": "fixed"})


__all__ = ["CurriculumAgent", "CurriculumProposal"]
