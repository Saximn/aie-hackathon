"""Failure diagnosis scaffold."""

from models import Diagnosis, FailureType, RecoveryTransition, VerificationResult, VerificationStatus


class Diagnoser:
    """Classifies why a non-successful verification result occurred."""

    def diagnose(self, verification: VerificationResult) -> Diagnosis:
        """Return a structured diagnosis.

        TODO(Person B): use GPT-5.5 with Structured Outputs to classify the
        failure from expected result, observed state, recent failures, and user
        coaching.
        """
        if verification.status == VerificationStatus.SUCCESS:
            return Diagnosis(
                action_id=verification.action_id,
                recommended_transition=RecoveryTransition.CONTINUE,
            )

        expected_text = " ".join(str(value).lower() for value in verification.expected.values())
        observed_text = " ".join(str(value).lower() for value in verification.observed.values())

        if "tree" in expected_text and "tree" not in observed_text:
            return Diagnosis(
                action_id=verification.action_id,
                failure_type=FailureType.VISUAL_MISALIGNMENT,
                confidence=0.65,
                cause="The target was expected to remain visible or centered, but the post-action observation did not confirm it.",
                repair="Re-observe the screen, recenter the nearest tree, and retry the movement or interaction.",
                should_research=False,
                recommended_transition=RecoveryTransition.RETRY,
            )

        return Diagnosis(
            action_id=verification.action_id,
            failure_type=FailureType.MISSING_STRATEGY,
            confidence=0.2,
            cause="The scaffold verifier could not map the failed action to a specific observable cause.",
            repair="Replan from a fresh World Snapshot and research only if the same failure repeats.",
            should_research=True,
            recommended_transition=RecoveryTransition.REPLAN,
        )
