"""GPT-5.5 planning scaffold."""

from __future__ import annotations

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

        TODO(Person B): call OpenAI Responses API with GPT-5.5 and Structured
        Outputs. The schema should be Plan, and every action must be one of the
        PrimitiveActionType values with explicit args, expected_result, and
        timeout_ms.
        """
        _ = (profile, memory_context, user_constraints)
        visible = {item.lower() for item in snapshot.visual.visible_objects}
        actions: list[PrimitiveAction]

        if "tree" in visible:
            actions = [
                PrimitiveAction(
                    id="a1",
                    type=PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT,
                    args={"object": "tree", "durationMs": 2000},
                    expected_result={"visual": "tree closer or centered"},
                    timeout_ms=3000,
                    adapter=AdapterKind.GENERIC_INPUT,
                ),
                PrimitiveAction(
                    id="a2",
                    type=PrimitiveActionType.INTERACT_PRIMARY,
                    args={"durationMs": 3000},
                    expected_result={"inventoryChange": "wood increased or block broken"},
                    timeout_ms=5000,
                    adapter=AdapterKind.GENERIC_INPUT,
                ),
            ]
        else:
            actions = [
                PrimitiveAction(
                    id="a1",
                    type=PrimitiveActionType.MOVE_MOUSE,
                    args={"dx": 240, "dy": 0},
                    expected_result={"visual": "new area scanned for trees or shelter resources"},
                    timeout_ms=1000,
                    adapter=AdapterKind.GENERIC_INPUT,
                ),
                PrimitiveAction(
                    id="a2",
                    type=PrimitiveActionType.WAIT,
                    args={"durationMs": 500},
                    expected_result={"visual": "screen stable after scan"},
                    timeout_ms=1000,
                    adapter=AdapterKind.GENERIC_INPUT,
                ),
            ]

        return Plan(
            plan_id=f"plan_{snapshot.cycle:03d}",
            goal=goal,
            snapshot_id=snapshot.snapshot_id,
            used_skills=[],
            actions=actions,
        )
