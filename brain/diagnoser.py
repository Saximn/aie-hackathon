"""Deterministic failure diagnosis rules."""

from models import Diagnosis, FailureType, RecoveryTransition, VerificationResult, VerificationStatus


class Diagnoser:
    """Classifies why a non-successful verification result occurred."""

    def diagnose(self, verification: VerificationResult) -> Diagnosis:
        """Return a structured diagnosis.

        TODO(Person B): use GPT-5.5 with Structured Outputs for ambiguous
        failures and deterministic rules for simple scaffold checks.
        """
        if verification.status == VerificationStatus.UNSAFE:
            return Diagnosis(
                action_id=verification.action_id,
                failure_type=FailureType.UNSAFE_STATE,
                confidence=verification.confidence,
                cause="Verification observed an unsafe game state.",
                repair="Abort the current plan and wait for explicit recovery instructions.",
                recommended_transition=RecoveryTransition.ABORT,
            )

        observed = " ".join(str(value).lower() for value in verification.observed.values())
        if "timeout" in observed:
            return Diagnosis(
                action_id=verification.action_id,
                failure_type=FailureType.TIMEOUT,
                confidence=max(verification.confidence, 0.8),
                cause="The action did not complete before its timeout.",
                repair="Retry the action once, then replan if the timeout repeats.",
                recommended_transition=RecoveryTransition.RETRY,
            )

        return Diagnosis(
            action_id=verification.action_id,
            confidence=verification.confidence,
            cause="The verification result does not match the expected outcome.",
            repair="Replan using the latest World Snapshot.",
            recommended_transition=RecoveryTransition.REPLAN,
        )
