"""Failure diagnosis scaffold."""

from models import Diagnosis, VerificationResult


class Diagnoser:
    """Classifies why a non-successful verification result occurred."""

    def diagnose(self, verification: VerificationResult) -> Diagnosis:
        """Return a structured diagnosis.

        TODO(Person B): use GPT-5.5 with Structured Outputs for ambiguous
        failures and deterministic rules for simple scaffold checks.
        """
        raise NotImplementedError("Diagnoser.diagnose is scaffold-only")
