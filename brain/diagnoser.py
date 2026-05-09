"""Diagnoser — coarse failure classification (stretch in OmniPlay-MC).

For the hackathon build the AgentLoop retries on failure without consulting
the diagnoser. We keep the module so the dashboard can show a `failure_type`
when the critic feedback maps clearly to one. A deeper LLM-driven diagnoser
is a Day 3 stretch goal documented in the plan.
"""

from __future__ import annotations

import asyncio
import uuid
import logging
from typing import TYPE_CHECKING

from models import Diagnosis, FailureType, RecoveryTransition, VerificationResult

if TYPE_CHECKING:
    from memory_store import MemoryStore

LOG = logging.getLogger("omniplay.diagnoser")

KEYWORD_TO_FAILURE: list[tuple[tuple[str, ...], FailureType]] = [
    (("not enough", "missing", "no axe", "no pickaxe", "need a"), FailureType.MISSING_PREREQUISITE),
    (("inventory full", "full inventory"), FailureType.INSUFFICIENT_RESOURCES),
    (("could not find", "no.*nearby", "couldn't find", "didn't find"), FailureType.RESOURCE_UNAVAILABLE),
    (("path", "stuck", "unreachable"), FailureType.PATHFINDING_FAILURE),
    (("timeout", "timed out"), FailureType.TIMEOUT),
    (("zombie", "skeleton", "creeper", "danger"), FailureType.UNSAFE_STATE),
]


class Diagnoser:
    def __init__(self, *, memory: MemoryStore | None = None) -> None:
        self._memory = memory

    def classify(self, *, verification: VerificationResult, action_id: str) -> Diagnosis:
        observed = verification.observed or {}
        text = " ".join(
            str(v) for v in (observed.get("runtime_error"), observed.get("feedback"), observed.get("runtime_result"))
            if v
        ).lower()
        failure: FailureType | None = None
        for keywords, ftype in KEYWORD_TO_FAILURE:
            if any(k in text for k in keywords):
                failure = ftype
                break
        diagnosis = Diagnosis(
            action_id=action_id,
            failure_type=failure,
            confidence=0.6 if failure else 0.0,
            cause=text[:200],
            repair=str(observed.get("feedback") or ""),
            should_research=False,
            recommended_transition=RecoveryTransition.REPLAN,
        )
        if self._memory is not None and failure is not None:
            self._schedule_lesson(diagnosis, triggered_by_task=action_id)
        return diagnosis

    def _schedule_lesson(self, diagnosis: Diagnosis, *, triggered_by_task: str) -> None:
        summary = diagnosis.repair or diagnosis.cause or str(diagnosis.failure_type)
        coro = self._memory.add_lesson(  # type: ignore[union-attr]
            lesson_id=str(uuid.uuid4()),
            summary=summary[:500],
            failure_type=diagnosis.failure_type.value if diagnosis.failure_type else None,
            triggered_by_task=triggered_by_task,
            code_excerpt=diagnosis.cause[:300] if diagnosis.cause else None,
        )
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            LOG.debug("no running loop; lesson not persisted for action %s", triggered_by_task)


__all__ = ["Diagnoser"]
