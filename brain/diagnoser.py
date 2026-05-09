"""Failure diagnosis scaffold."""

from models import Diagnosis, FailureType, RecoveryTransition, VerificationResult, VerificationStatus


class Diagnoser:
    """Classifies why a non-successful verification result occurred."""

    def diagnose(self, verification: VerificationResult) -> Diagnosis:
        # TODO(Person B): map observable failures to specific failure types.
        if verification.status == VerificationStatus.SUCCESS:
            return Diagnosis(action_id=verification.action_id, recommended_transition=RecoveryTransition.CONTINUE)
        return Diagnosis(
            action_id=verification.action_id,
            failure_type=FailureType.MISSING_STRATEGY,
            confidence=0.1,
            reason="TODO: diagnosis not implemented",
            recommended_transition=RecoveryTransition.REPLAN,
        )
