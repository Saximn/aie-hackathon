"""Verification scaffold."""

from models import ExecutionResult, PrimitiveAction, VerificationResult, VerificationStatus, WorldSnapshot


class Verifier:
    """Compares expected results against a fresh post-action WorldSnapshot."""

    def verify(self, action: PrimitiveAction, result: ExecutionResult, post_snapshot: WorldSnapshot) -> VerificationResult:
        # TODO(Person B): compare action.expected_result with post_snapshot.
        status = VerificationStatus.SUCCESS if result.success else VerificationStatus.FAILED
        return VerificationResult(action_id=action.id, status=status, expected=action.expected_result, evidence=result.evidence)
