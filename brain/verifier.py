"""Verification scaffold."""

from models import ExecutionResult, PrimitiveAction, VerificationResult, WorldSnapshot


class Verifier:
    """Compares expected results against a fresh post-action WorldSnapshot."""

    def verify(
        self,
        action: PrimitiveAction,
        result: ExecutionResult,
        post_snapshot: WorldSnapshot,
    ) -> VerificationResult:
        raise NotImplementedError("Verifier.verify is scaffold-only")
