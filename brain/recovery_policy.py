"""Recovery transition recommendation rules."""

from models import Diagnosis, RecoveryTransition, VerificationResult, VerificationStatus


class RecoveryPolicy:
    """Maps verification and diagnosis into the next AgentLoop transition."""

    def recommend(self, verification: VerificationResult, diagnosis: Diagnosis) -> RecoveryTransition:
        if verification.status == VerificationStatus.SUCCESS:
            return RecoveryTransition.CONTINUE

        if verification.status == VerificationStatus.UNSAFE:
            return RecoveryTransition.ABORT

        if diagnosis.should_research:
            return RecoveryTransition.RESEARCH

        return diagnosis.recommended_transition
