"""Diagnoser — coarse failure classification (stretch in OmniPlay-MC).

For the hackathon build the AgentLoop retries on failure without consulting
the diagnoser. We keep the module so the dashboard can show a `failure_type`
when the critic feedback maps clearly to one. A deeper LLM-driven diagnoser
is a Day 3 stretch goal documented in the plan.
"""

from __future__ import annotations

from models import Diagnosis, FailureType, RecoveryTransition, VerificationResult

KEYWORD_TO_FAILURE: list[tuple[tuple[str, ...], FailureType]] = [
    (("not enough", "missing", "no axe", "no pickaxe", "need a"), FailureType.MISSING_PREREQUISITE),
    (("inventory full", "full inventory"), FailureType.INSUFFICIENT_RESOURCES),
    (("could not find", "no.*nearby", "couldn't find", "didn't find"), FailureType.RESOURCE_UNAVAILABLE),
    (("path", "stuck", "unreachable"), FailureType.PATHFINDING_FAILURE),
    (("timeout", "timed out"), FailureType.TIMEOUT),
    (("zombie", "skeleton", "creeper", "danger"), FailureType.UNSAFE_STATE),
]


class Diagnoser:
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
        return Diagnosis(
            action_id=action_id,
            failure_type=failure,
            confidence=0.6 if failure else 0.0,
            cause=text[:200],
            repair=str(observed.get("feedback") or ""),
            should_research=False,
            recommended_transition=RecoveryTransition.REPLAN,
        )


__all__ = ["Diagnoser"]
