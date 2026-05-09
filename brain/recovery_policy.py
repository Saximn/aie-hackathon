"""Recovery transition recommendation scaffold."""

from models import Diagnosis, FailureType, RecoveryTransition, VerificationResult, VerificationStatus


class RecoveryPolicy:
    """Maps verification and diagnosis into the next AgentLoop transition."""

    def recommend(self, verification: VerificationResult, diagnosis: Diagnosis) -> RecoveryTransition:
        if verification.status == VerificationStatus.SUCCESS:
            return RecoveryTransition.CONTINUE
        if verification.status == VerificationStatus.UNSAFE:
            return RecoveryTransition.ABORT
        if diagnosis.should_research or diagnosis.failure_type == FailureType.MISSING_STRATEGY:
            return RecoveryTransition.RESEARCH
        if diagnosis.failure_type in {FailureType.VISUAL_MISALIGNMENT, FailureType.TIMEOUT}:
            return RecoveryTransition.RETRY
        if verification.status == VerificationStatus.INVALID_PLAN:
            return RecoveryTransition.REPLAN
        return diagnosis.recommended_transition
