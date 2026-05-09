"""Verification scaffold."""

from models import ExecutionResult, PrimitiveAction, VerificationResult, VerificationStatus, WorldSnapshot


class Verifier:
    """Compares expected results against a fresh post-action WorldSnapshot."""

    def verify(
        self,
        action: PrimitiveAction,
        result: ExecutionResult,
        post_snapshot: WorldSnapshot,
    ) -> VerificationResult:
        observed = {
            "executionResult": result.result,
            "visual": post_snapshot.visual.model_dump(mode="json"),
            "symbolic": post_snapshot.symbolic.model_dump(mode="json"),
        }

        if not result.success:
            return VerificationResult(
                action_id=action.id,
                status=VerificationStatus.FAILED,
                expected=action.expected_result,
                observed=observed,
                confidence=0.6,
            )

        return VerificationResult(
            action_id=action.id,
            status=VerificationStatus.SUCCESS,
            expected=action.expected_result,
            observed=observed,
            confidence=max(post_snapshot.visual.confidence, 0.5),
        )
