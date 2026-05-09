"""RecoveryPolicy — maps a verification outcome onto the next AgentLoop transition."""

from __future__ import annotations

from models import RecoveryTransition, VerificationResult, VerificationStatus

MAX_RETRIES = 3


class RecoveryPolicy:
    def decide(
        self,
        *,
        verification: VerificationResult,
        attempts_for_task: int,
    ) -> RecoveryTransition:
        if verification.status == VerificationStatus.SUCCESS:
            return RecoveryTransition.STORE_MEMORY
        if attempts_for_task >= MAX_RETRIES:
            return RecoveryTransition.ABORT
        if verification.status in (
            VerificationStatus.FAILED,
            VerificationStatus.INCOMPLETE,
            VerificationStatus.STUCK,
        ):
            return RecoveryTransition.REPLAN
        if verification.status == VerificationStatus.UNSAFE:
            return RecoveryTransition.ABORT
        if verification.status == VerificationStatus.INVALID_PLAN:
            return RecoveryTransition.REPLAN
        return RecoveryTransition.REPLAN


__all__ = ["RecoveryPolicy"]
