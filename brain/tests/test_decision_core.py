from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from diagnoser import Diagnoser
from game_profile_builder import GameProfileBuilder
from models import (
    AdapterKind,
    ExecutionResult,
    FailureType,
    Plan,
    PrimitiveAction,
    PrimitiveActionType,
    RecoveryTransition,
    ResearchNote,
    SymbolicObservation,
    VerificationResult,
    VerificationStatus,
    VisualObservation,
    WorldSnapshot,
)
from observer import Observer
from planner import Planner
from recovery_policy import RecoveryPolicy
from researcher import Researcher
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


def test_skill_builder_turns_researched_guidance_into_candidate_skill() -> None:
    note = ResearchNote(
        query="minecraft first night shelter",
        summary="Collect wood, craft planks, and build a shelter before night mobs spawn.",
        source_urls=["https://example.test/shelter"],
        confidence=0.75,
    )

    skill = SkillBuilder().from_guidance("survive_first_night", note)

    assert skill.name == "survive_first_night"
    assert skill.source == "researched"
    assert skill.status == "candidate"
    assert [action.type for action in skill.ordered_actions] == [
        PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT,
        PrimitiveActionType.COLLECT_BLOCK,
        PrimitiveActionType.CRAFT_ITEM,
        PrimitiveActionType.BUILD_SHELTER,
    ]
    assert "visible_object: shelter" in skill.success_criteria
    assert skill.failure_modes


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


def test_planner_creates_grounded_first_night_demo_plan() -> None:
    import asyncio

    profile = asyncio.run(GameProfileBuilder().build("minecraft"))
    snapshot = WorldSnapshot(
        snapshot_id="snapshot-1",
        cycle=1,
        game="minecraft",
        goal="survive_first_night",
        visual=VisualObservation(visible_objects=["tree"], risk_level="low", time_of_day="day", confidence=0.8),
    )

    plan = asyncio.run(
        Planner().plan(
            "survive_first_night",
            profile,
            snapshot,
            memory_context="Prefer collecting wood before shelter.",
            user_constraints=["avoid fast combat"],
        )
    )

    assert plan.goal == "survive_first_night"
    assert plan.snapshot_id == "snapshot-1"
    assert [action.type for action in plan.actions] == [
        PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT,
        PrimitiveActionType.COLLECT_BLOCK,
        PrimitiveActionType.CRAFT_ITEM,
        PrimitiveActionType.BUILD_SHELTER,
    ]
    assert Validator().validate_plan(plan).status == RecoveryTransition.CONTINUE


def test_observer_builds_world_snapshot_from_visual_and_symbolic_runtime_data() -> None:
    import asyncio

    class FakeBotClient:
        async def screenshot_b64(self) -> str:
            return "png-data"

        async def state(self) -> dict:
            return {
                "health": 18,
                "hunger": 5,
                "inventory": {"wood": 2},
                "nearby_blocks": ["tree"],
                "nearby_entities": ["zombie"],
                "biome": "forest",
            }

    class FakeVision:
        async def observe(self, screenshot_b64, goal, game) -> VisualObservation:
            return VisualObservation(
                scene_summary="Forest with a tree and hostile mob.",
                visible_objects=["tree", "zombie"],
                risk_level="medium",
                time_of_day="night",
                ui_state="gameplay",
                confidence=0.8,
            )

    snapshot = asyncio.run(Observer(FakeBotClient(), FakeVision()).observe(2, "survive_first_night", "minecraft"))

    assert snapshot.snapshot_id == "minecraft:2"
    assert snapshot.screenshot_b64 == "png-data"
    assert snapshot.visual.visible_objects == ["tree", "zombie"]
    assert snapshot.symbolic.inventory == {"wood": 2}
    assert snapshot.derived_risks.night_risk == "high"
    assert snapshot.derived_risks.combat_risk == "high"
    assert snapshot.derived_risks.food_risk == "high"


def test_observer_degrades_to_empty_symbolic_state_when_runtime_unavailable() -> None:
    import asyncio

    class FailingBotClient:
        async def screenshot_b64(self) -> str:
            raise RuntimeError("runtime down")

        async def state(self) -> dict:
            raise RuntimeError("runtime down")

    snapshot = asyncio.run(Observer(FailingBotClient()).observe(1, "collect wood", "minecraft"))

    assert snapshot.screenshot_b64 is None
    assert snapshot.symbolic.inventory == {}
    assert snapshot.visual.confidence == 0.0
    assert snapshot.derived_risks.night_risk == "unknown"


def test_game_profile_builder_returns_static_demo_profiles_and_unknown_fallback() -> None:
    import asyncio

    minecraft = asyncio.run(GameProfileBuilder().build("Minecraft"))
    minetest = asyncio.run(GameProfileBuilder().build("minetest"))
    unknown = asyncio.run(GameProfileBuilder().build("Veloren"))

    assert minecraft.source == "static"
    assert minecraft.confidence >= 0.9
    assert "survive_first_night" in minecraft.benchmark_goals
    assert "primary_action" in minecraft.controls
    assert AdapterKind.MINECRAFT in minecraft.adapter_hints

    assert minetest.source == "static"
    assert minetest.confidence >= 0.8
    assert "survive_first_night" in minetest.benchmark_goals
    assert minetest.controls["inventory"] == "i"

    assert unknown.game_name == "veloren"
    assert unknown.source == "fallback"
    assert unknown.confidence < 0.4


def test_game_profile_builder_merges_research_without_overwriting_static_defaults() -> None:
    import asyncio

    note = ResearchNote(
        query="veloren early survival",
        summary="- Survival sandbox with WASD keyboard controls\n- Collect wood early before night",
        source_urls=["https://example.test/guide"],
        confidence=0.7,
    )

    researched = asyncio.run(GameProfileBuilder().build("veloren", [note]))
    minecraft = asyncio.run(GameProfileBuilder().build("minecraft", [note]))

    assert researched.source == "researched"
    assert researched.confidence == 0.7
    assert researched.controls["move"] == "WASD"
    assert "Collect wood early before night" in researched.early_game_objectives

    assert minecraft.source == "static"
    assert minecraft.confidence == 0.95
    assert minecraft.controls["inventory"] == "e"
    assert "Survival sandbox with WASD keyboard controls" in minecraft.core_mechanics


def test_researcher_returns_structured_notes_and_controls_provider_failures() -> None:
    import asyncio

    class FakeProvider:
        async def search(self, query: str) -> ResearchNote:
            return ResearchNote(
                query=query,
                summary=" Gather wood before night. ",
                source_urls=[" https://example.test/a ", "https://example.test/a"],
                confidence=1.4,
            )

    class FailingProvider:
        async def search(self, query: str) -> ResearchNote:
            raise RuntimeError("secret provider detail")

    note = asyncio.run(Researcher(FakeProvider()).research(" minecraft   first night "))
    failed = asyncio.run(Researcher(FailingProvider()).research("minecraft first night"))

    assert note.query == "minecraft first night"
    assert note.summary == "Gather wood before night."
    assert note.source_urls == ["https://example.test/a"]
    assert note.confidence == 1.0

    assert failed.confidence == 0.0
    assert failed.source_urls == []
    assert failed.summary == "Research unavailable: RuntimeError"
