"""Expected-result verification rules."""

from typing import Any

from models import ExecutionResult, PrimitiveAction, VerificationResult, VerificationStatus, WorldSnapshot


class Verifier:
    """Compares expected results against a fresh post-action WorldSnapshot."""

    def verify(
        self,
        action: PrimitiveAction,
        result: ExecutionResult,
        post_snapshot: WorldSnapshot,
    ) -> VerificationResult:
        if not result.success:
            return VerificationResult(
                action_id=action.id,
                status=VerificationStatus.FAILED,
                expected=action.expected_result,
                observed={"result": result.result, **result.evidence},
                confidence=1.0,
            )

        observed = _observed_snapshot_state(post_snapshot)
        if observed["risk_level"] == "high":
            return VerificationResult(
                action_id=action.id,
                status=VerificationStatus.UNSAFE,
                expected=action.expected_result,
                observed=observed,
                confidence=_snapshot_confidence(post_snapshot),
            )

        if _expectations_match(action.expected_result, observed):
            return VerificationResult(
                action_id=action.id,
                status=VerificationStatus.SUCCESS,
                expected=action.expected_result,
                observed=observed,
                confidence=_snapshot_confidence(post_snapshot),
            )

        return VerificationResult(
            action_id=action.id,
            status=VerificationStatus.FAILED,
            expected=action.expected_result,
            observed=observed,
            confidence=_snapshot_confidence(post_snapshot),
        )


def _observed_snapshot_state(snapshot: WorldSnapshot) -> dict[str, Any]:
    return {
        "visible_objects": snapshot.visual.visible_objects,
        "ui_state": snapshot.visual.ui_state,
        "risk_level": snapshot.visual.risk_level,
        "time_of_day": snapshot.visual.time_of_day,
        "inventory": snapshot.symbolic.inventory,
    }


def _expectations_match(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    for key, expected_value in expected.items():
        if key == "visible_object":
            visible_objects = [str(item).lower() for item in observed["visible_objects"]]
            if str(expected_value).lower() not in visible_objects:
                return False
            continue

        if key == "inventory_contains":
            if not _inventory_contains(observed["inventory"], expected_value):
                return False
            continue

        if observed.get(key) != expected_value:
            return False

    return True


def _inventory_contains(inventory: dict[str, int], expected_value: Any) -> bool:
    if not isinstance(expected_value, dict):
        return False

    for item, count in expected_value.items():
        if not isinstance(count, int | float):
            return False
        if inventory.get(str(item), 0) < count:
            return False

    return True


def _snapshot_confidence(snapshot: WorldSnapshot) -> float:
    return snapshot.visual.confidence or 1.0
