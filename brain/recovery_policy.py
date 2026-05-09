"""Recovery policy scaffold."""

from models import Diagnosis, RecoveryTransition, VerificationResult, VerificationStatus


class RecoveryPolicy:
    """Recommends the next AgentLoop transition."""

    def choose(self, verification: VerificationResult, diagnosis: Diagnosis | None = None) -> RecoveryTransition:
        # TODO(Person B): encode retry, replan, research, abort, and memory rules.
        if verification.status == VerificationStatus.SUCCESS:
            return RecoveryTransition.CONTINUE
        if diagnosis:
            return diagnosis.recommended_transition
        return RecoveryTransition.REPLAN
