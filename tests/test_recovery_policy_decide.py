"""TDD Slice 0 — RecoveryPolicy.decide behaviour tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "brain"))

from models import RecoveryTransition, VerificationResult, VerificationStatus
from recovery_policy import RecoveryPolicy


def _vr(status: VerificationStatus) -> VerificationResult:
    return VerificationResult(action_id="action-1", status=status)


def test_decide_success_returns_store_memory() -> None:
    result = RecoveryPolicy().decide(
        verification=_vr(VerificationStatus.SUCCESS),
        attempts_for_task=0,
    )
    assert result == RecoveryTransition.STORE_MEMORY


def test_decide_failed_returns_replan_below_max_retries() -> None:
    policy = RecoveryPolicy()
    for attempts in (0, 1, 2):
        result = policy.decide(
            verification=_vr(VerificationStatus.FAILED),
            attempts_for_task=attempts,
        )
        assert result == RecoveryTransition.REPLAN, f"expected REPLAN at attempts={attempts}"


def test_decide_failed_returns_abort_at_max_retries() -> None:
    policy = RecoveryPolicy()
    for attempts in (3, 4, 10):
        result = policy.decide(
            verification=_vr(VerificationStatus.FAILED),
            attempts_for_task=attempts,
        )
        assert result == RecoveryTransition.ABORT, f"expected ABORT at attempts={attempts}"


def test_decide_incomplete_replans_then_aborts() -> None:
    policy = RecoveryPolicy()
    for attempts in (0, 1, 2):
        assert policy.decide(
            verification=_vr(VerificationStatus.INCOMPLETE),
            attempts_for_task=attempts,
        ) == RecoveryTransition.REPLAN, f"expected REPLAN at attempts={attempts}"
    for attempts in (3, 5):
        assert policy.decide(
            verification=_vr(VerificationStatus.INCOMPLETE),
            attempts_for_task=attempts,
        ) == RecoveryTransition.ABORT, f"expected ABORT at attempts={attempts}"


def test_decide_stuck_replans_then_aborts() -> None:
    policy = RecoveryPolicy()
    for attempts in (0, 1, 2):
        assert policy.decide(
            verification=_vr(VerificationStatus.STUCK),
            attempts_for_task=attempts,
        ) == RecoveryTransition.REPLAN, f"expected REPLAN at attempts={attempts}"
    for attempts in (3, 5):
        assert policy.decide(
            verification=_vr(VerificationStatus.STUCK),
            attempts_for_task=attempts,
        ) == RecoveryTransition.ABORT, f"expected ABORT at attempts={attempts}"


def test_decide_invalid_plan_replans_until_cap() -> None:
    policy = RecoveryPolicy()
    for attempts in (0, 1, 2):
        assert policy.decide(
            verification=_vr(VerificationStatus.INVALID_PLAN),
            attempts_for_task=attempts,
        ) == RecoveryTransition.REPLAN, f"expected REPLAN at attempts={attempts}"
    for attempts in (3, 4):
        assert policy.decide(
            verification=_vr(VerificationStatus.INVALID_PLAN),
            attempts_for_task=attempts,
        ) == RecoveryTransition.ABORT, f"expected ABORT at attempts={attempts}"


def test_decide_unsafe_aborts_immediately() -> None:
    result = RecoveryPolicy().decide(
        verification=_vr(VerificationStatus.UNSAFE),
        attempts_for_task=0,
    )
    assert result == RecoveryTransition.ABORT
