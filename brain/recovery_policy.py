"""Recovery transition recommendation scaffold."""

from models import Diagnosis, RecoveryTransition, VerificationResult


class RecoveryPolicy:
    """Maps verification and diagnosis into the next AgentLoop transition."""

    def recommend(self, verification: VerificationResult, diagnosis: Diagnosis) -> RecoveryTransition:
        raise NotImplementedError("RecoveryPolicy.recommend is scaffold-only")
