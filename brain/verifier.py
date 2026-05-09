"""Verifier — wraps the CriticAgent's verdict into a VerificationResult."""

from __future__ import annotations

import logging
from typing import Any

from models import VerificationResult, VerificationStatus
from voyager_agents import CriticAgent, CriticVerdict

LOG = logging.getLogger("omniplay.verifier")


VERDICT_TO_STATUS: dict[str, VerificationStatus] = {
    "success": VerificationStatus.SUCCESS,
    "incomplete": VerificationStatus.INCOMPLETE,
    "failed": VerificationStatus.FAILED,
}


class Verifier:
    def __init__(self, *, critic: CriticAgent | None = None) -> None:
        self.critic = critic or CriticAgent()

    def verify(
        self,
        *,
        action_id: str,
        task: str,
        code: str,
        runtime_ok: bool,
        runtime_error: str | None,
        runtime_result: str | None,
        snapshot_before: dict[str, Any],
        snapshot_after: dict[str, Any],
    ) -> tuple[VerificationResult, CriticVerdict]:
        verdict = self.critic.judge(
            task=task,
            code=code,
            runtime_ok=runtime_ok,
            runtime_error=runtime_error,
            runtime_result=runtime_result,
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_after,
        )
        status = VERDICT_TO_STATUS.get(verdict.verdict, VerificationStatus.FAILED)
        verification = VerificationResult(
            action_id=action_id,
            status=status,
            expected={"task": task},
            observed={
                "runtime_ok": runtime_ok,
                "runtime_error": runtime_error,
                "runtime_result": runtime_result,
                "feedback": verdict.feedback,
            },
            confidence=verdict.confidence,
        )
        return verification, verdict


__all__ = ["Verifier"]
