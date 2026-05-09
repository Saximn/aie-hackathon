from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from diagnoser import Diagnoser
from models import (
    AdapterKind,
    ExecutionResult,
    FailureType,
    Plan,
    PrimitiveAction,
    PrimitiveActionType,
    RecoveryTransition,
    SymbolicObservation,
    VerificationResult,
    VerificationStatus,
    VisualObservation,
    WorldSnapshot,
)
from recovery_policy import RecoveryPolicy
from skill_builder import SkillBuilder
from verifier import Verifier
from validator import Validator


def primitive_action(action_id: str, action_type: PrimitiveActionType, **args) -> PrimitiveAction:
    return PrimitiveAction(
        id=action_id,
        type=action_type,
        args=args,
        expected_result={"observable": "state change"},
        timeout_ms=1000,
        adapter=AdapterKind.GENERIC_INPUT,
    )


def test_validator_accepts_grounded_plan() -> None:
    plan = Plan(
        plan_id="plan-1",
        goal="collect visible wood",
        snapshot_id="snapshot-1",
        actions=[
            primitive_action("look", PrimitiveActionType.MOVE_MOUSE, dx=15, dy=0),
            primitive_action("forward", PrimitiveActionType.HOLD_KEY, key="w", duration_ms=500),
        ],
    )

    result = Validator().validate_plan(plan)

    assert result.status == RecoveryTransition.CONTINUE
    assert result.reason == ""


def test_validator_replans_empty_plan() -> None:
    plan = Plan(
        plan_id="plan-1",
        goal="collect visible wood",
        snapshot_id="snapshot-1",
        actions=[],
    )

    result = Validator().validate_plan(plan)

    assert result.status == RecoveryTransition.REPLAN
    assert "at least one action" in result.reason


def test_validator_replans_vague_action() -> None:
    plan = Plan(
        plan_id="plan-1",
        goal="look toward a tree",
        snapshot_id="snapshot-1",
        actions=[
            PrimitiveAction(
                id="look",
                type=PrimitiveActionType.MOVE_MOUSE,
                args={},
                expected_result={"visible_object": "tree"},
                timeout_ms=1000,
                adapter=AdapterKind.GENERIC_INPUT,
            )
        ],
    )

    result = Validator().validate_plan(plan)

    assert result.status == RecoveryTransition.REPLAN
    assert "move_mouse" in result.reason
    assert "dx" in result.reason


def test_validator_replans_boolean_numeric_args() -> None:
    action = PrimitiveAction(
        id="look",
        type=PrimitiveActionType.MOVE_MOUSE,
        args={"dx": True, "dy": 0},
        expected_result={"visible_object": "tree"},
    )

    result = Validator().validate_action(action)

    assert result.status == RecoveryTransition.REPLAN
    assert "dx" in result.reason


def test_validator_replans_duplicate_action_ids() -> None:
    plan = Plan(
        plan_id="plan-1",
        goal="collect visible wood",
        snapshot_id="snapshot-1",
        actions=[
            primitive_action("collect", PrimitiveActionType.COLLECT_BLOCK, block="wood"),
            primitive_action("collect", PrimitiveActionType.COLLECT_BLOCK, block="stone"),
        ],
    )

    result = Validator().validate_plan(plan)

    assert result.status == RecoveryTransition.REPLAN
    assert "duplicate action id" in result.reason


def test_validator_replans_unconfigured_adapter_action_args() -> None:
    action = PrimitiveAction(
        id="shelter",
        type=PrimitiveActionType.BUILD_SHELTER,
        args={},
        expected_result={"visible_object": "shelter"},
    )

    result = Validator().validate_action(action)

    assert result.status == RecoveryTransition.REPLAN
    assert "build_shelter" in result.reason


def test_diagnoser_retries_timeout_verification() -> None:
    verification = VerificationResult(
        action_id="forward",
        status=VerificationStatus.FAILED,
        expected={"visible_object": "tree"},
        observed={"error": "runtime timeout waiting for movement"},
        confidence=0.9,
    )

    diagnosis = Diagnoser().diagnose(verification)

    assert diagnosis.failure_type == FailureType.TIMEOUT
    assert diagnosis.recommended_transition == RecoveryTransition.RETRY
    assert diagnosis.action_id == "forward"


def test_diagnoser_aborts_unsafe_verification() -> None:
    verification = VerificationResult(
        action_id="move",
        status=VerificationStatus.UNSAFE,
        expected={"risk_level": "low"},
        observed={"risk_level": "high", "threat": "lava"},
        confidence=0.95,
    )

    diagnosis = Diagnoser().diagnose(verification)

    assert diagnosis.failure_type == FailureType.UNSAFE_STATE
    assert diagnosis.recommended_transition == RecoveryTransition.ABORT
    assert diagnosis.confidence == 0.95


def test_recovery_policy_researches_when_diagnosis_needs_knowledge() -> None:
    verification = VerificationResult(
        action_id="craft",
        status=VerificationStatus.FAILED,
        expected={"crafted": "stone_pickaxe"},
        observed={"missing": "recipe"},
        confidence=0.7,
    )
    diagnosis = Diagnoser().diagnose(verification)
    diagnosis.should_research = True
    diagnosis.failure_type = FailureType.MISSING_STRATEGY

    transition = RecoveryPolicy().recommend(verification, diagnosis)

    assert transition == RecoveryTransition.RESEARCH


def test_skill_builder_turns_plan_into_candidate_skill() -> None:
    plan = Plan(
        plan_id="plan-1",
        goal="collect visible wood",
        snapshot_id="snapshot-1",
        actions=[
            primitive_action("approach", PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT, object="tree"),
            primitive_action("collect", PrimitiveActionType.COLLECT_BLOCK, block="wood"),
        ],
    )

    skill = SkillBuilder().from_plan(plan)

    assert skill.name == "collect_visible_wood"
    assert skill.goal == "collect visible wood"
    assert [action.type for action in skill.ordered_actions] == [
        PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT,
        PrimitiveActionType.COLLECT_BLOCK,
    ]
    assert skill.success_criteria == ["observable: state change", "observable: state change"]


def test_skill_builder_promotes_successful_skill_without_mutating_original() -> None:
    original = SkillBuilder().from_plan(
        Plan(
            plan_id="plan-1",
            goal="collect visible wood",
            snapshot_id="snapshot-1",
            actions=[primitive_action("collect", PrimitiveActionType.COLLECT_BLOCK, block="wood")],
        )
    )

    promoted = SkillBuilder().promote_after_success(original)

    assert promoted.name == original.name
    assert promoted.version == 2
    assert promoted.status == "verified"
    assert promoted.confidence > original.confidence
    assert original.version == 1
    assert original.status == "candidate"


def test_verifier_fails_when_execution_fails() -> None:
    action = primitive_action("collect", PrimitiveActionType.COLLECT_BLOCK, block="wood")
    result = ExecutionResult(
        action_id="collect",
        success=False,
        result="runtime rejected action",
        evidence={"error": "unsupported action"},
    )

    verification = Verifier().verify(
        action,
        result,
        WorldSnapshot(snapshot_id="snapshot-2", cycle=1, game="minecraft", goal="collect wood"),
    )

    assert verification.status == VerificationStatus.FAILED
    assert verification.observed["result"] == "runtime rejected action"
    assert verification.observed["error"] == "unsupported action"


def test_verifier_succeeds_when_expected_visible_object_is_seen() -> None:
    action = PrimitiveAction(
        id="look",
        type=PrimitiveActionType.MOVE_MOUSE,
        args={"dx": 10, "dy": 0},
        expected_result={"visible_object": "tree"},
    )
    result = ExecutionResult(action_id="look", success=True, result="ok")
    snapshot = WorldSnapshot(
        snapshot_id="snapshot-2",
        cycle=1,
        game="minecraft",
        goal="collect wood",
        visual=VisualObservation(visible_objects=["tree", "grass"], confidence=0.8),
    )

    verification = Verifier().verify(action, result, snapshot)

    assert verification.status == VerificationStatus.SUCCESS
    assert verification.observed["visible_objects"] == ["tree", "grass"]
    assert verification.confidence == 0.8


def test_verifier_fails_when_inventory_expectation_is_not_met() -> None:
    action = PrimitiveAction(
        id="collect",
        type=PrimitiveActionType.COLLECT_BLOCK,
        args={"block": "wood"},
        expected_result={"inventory_contains": {"wood": 3}},
    )
    result = ExecutionResult(action_id="collect", success=True, result="ok")
    snapshot = WorldSnapshot(
        snapshot_id="snapshot-2",
        cycle=1,
        game="minecraft",
        goal="collect wood",
        symbolic=SymbolicObservation(inventory={"wood": 1}),
    )

    verification = Verifier().verify(action, result, snapshot)

    assert verification.status == VerificationStatus.FAILED
    assert verification.observed["inventory"] == {"wood": 1}


def test_verifier_succeeds_when_inventory_contains_enough_items() -> None:
    action = PrimitiveAction(
        id="collect",
        type=PrimitiveActionType.COLLECT_BLOCK,
        args={"block": "wood"},
        expected_result={"inventory_contains": {"wood": 3}},
    )
    result = ExecutionResult(action_id="collect", success=True, result="ok")
    snapshot = WorldSnapshot(
        snapshot_id="snapshot-2",
        cycle=1,
        game="minecraft",
        goal="collect wood",
        symbolic=SymbolicObservation(inventory={"wood": 4, "stick": 1}),
    )

    verification = Verifier().verify(action, result, snapshot)

    assert verification.status == VerificationStatus.SUCCESS
    assert verification.observed["inventory"] == {"wood": 4, "stick": 1}


def test_verifier_marks_high_risk_snapshot_unsafe() -> None:
    action = primitive_action("move", PrimitiveActionType.HOLD_KEY, key="w", duration_ms=500)
    result = ExecutionResult(action_id="move", success=True, result="ok")
    snapshot = WorldSnapshot(
        snapshot_id="snapshot-2",
        cycle=1,
        game="minecraft",
        goal="avoid lava",
        visual=VisualObservation(risk_level="high", confidence=0.85),
    )

    verification = Verifier().verify(action, result, snapshot)

    assert verification.status == VerificationStatus.UNSAFE
    assert verification.observed["risk_level"] == "high"
