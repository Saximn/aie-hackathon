"""Planner implementations for grounded demo Plans."""

from __future__ import annotations

from uuid import uuid4

from models import AdapterKind, GameProfile, Plan, PrimitiveAction, PrimitiveActionType, WorldSnapshot


class Planner:
    """Produces grounded Plans from profiles, snapshots, memory, and skills."""

    async def plan(
        self,
        goal: str,
        profile: GameProfile,
        snapshot: WorldSnapshot,
        memory_context: str,
        user_constraints: list[str] | None = None,
    ) -> Plan:
        """Create a grounded plan.

        The hackathon demo uses deterministic planning so the Brain can run
        without API keys. A later OpenAI-backed planner can keep this public
        interface and replace only the implementation behind it.
        """
        normalized_goal = goal.strip().lower()
        constraints = [constraint.lower() for constraint in user_constraints or []]

        if "survive_first_night" in normalized_goal or "first night" in normalized_goal:
            actions = _first_night_actions(profile, snapshot, constraints)
        elif "wood" in normalized_goal or "tree" in normalized_goal:
            actions = _collect_wood_actions(profile, snapshot)
        else:
            actions = _orientation_actions(snapshot)

        return Plan(
            plan_id=f"plan-{uuid4()}",
            goal=goal,
            snapshot_id=snapshot.snapshot_id,
            used_skills=_used_skills(memory_context),
            actions=actions,
        )


def _first_night_actions(
    profile: GameProfile,
    snapshot: WorldSnapshot,
    constraints: list[str],
) -> list[PrimitiveAction]:
    actions = _collect_wood_actions(profile, snapshot)
    shelter_material = "wood" if profile.game_name == "minecraft" else "wood"
    actions.extend(
        [
            PrimitiveAction(
                id="craft_starter_planks",
                type=PrimitiveActionType.CRAFT_ITEM,
                args={"item": "wooden_planks"},
                expected_result={"inventory_contains": {"wooden_planks": 1}},
                adapter=_preferred_adapter(profile),
            ),
            PrimitiveAction(
                id="build_basic_shelter",
                type=PrimitiveActionType.BUILD_SHELTER,
                args={"material": shelter_material},
                expected_result={"visible_object": "shelter"},
                adapter=_preferred_adapter(profile),
                timeout_ms=5000,
            ),
        ]
    )

    if any("avoid fast combat" in constraint for constraint in constraints):
        for action in actions:
            action.expected_result.setdefault("risk_level", "low")

    return actions


def _collect_wood_actions(profile: GameProfile, snapshot: WorldSnapshot) -> list[PrimitiveAction]:
    target = _wood_target(snapshot, profile)
    return [
        PrimitiveAction(
            id=f"approach_{target}",
            type=PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT,
            args={"object": target},
            expected_result={"visible_object": target},
            timeout_ms=4000,
        ),
        PrimitiveAction(
            id="collect_wood",
            type=PrimitiveActionType.COLLECT_BLOCK,
            args={"block": "wood"},
            expected_result={"inventory_contains": {"wood": 1}},
            adapter=_preferred_adapter(profile),
            timeout_ms=5000,
        ),
    ]


def _orientation_actions(snapshot: WorldSnapshot) -> list[PrimitiveAction]:
    expected_result = {}
    if snapshot.visual.visible_objects:
        expected_result["visible_object"] = snapshot.visual.visible_objects[0]

    return [
        PrimitiveAction(
            id="scan_area",
            type=PrimitiveActionType.MOVE_MOUSE,
            args={"dx": 20, "dy": 0},
            expected_result=expected_result,
        )
    ]


def _wood_target(snapshot: WorldSnapshot, profile: GameProfile) -> str:
    visible = {item.lower() for item in snapshot.visual.visible_objects}
    if "tree" in visible:
        return "tree"
    if "wood" in visible:
        return "wood"
    if profile.game_name == "minetest":
        return "tree"
    return "tree"


def _preferred_adapter(profile: GameProfile) -> AdapterKind:
    if AdapterKind.MINECRAFT in profile.adapter_hints:
        return AdapterKind.MINECRAFT
    return AdapterKind.GENERIC_INPUT


def _used_skills(memory_context: str) -> list[str]:
    if not memory_context:
        return []
    return ["memory_context"]
