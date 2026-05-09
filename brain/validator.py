"""Plan and action validation scaffold."""

from __future__ import annotations

from dataclasses import dataclass

from models import AdapterKind, Plan, PrimitiveAction, PrimitiveActionType, RecoveryTransition


GENERIC_ACTIONS = {
    PrimitiveActionType.PRESS_KEY,
    PrimitiveActionType.HOLD_KEY,
    PrimitiveActionType.MOVE_MOUSE,
    PrimitiveActionType.CLICK,
    PrimitiveActionType.WAIT,
    PrimitiveActionType.OPEN_MENU,
    PrimitiveActionType.SELECT_HOTBAR_SLOT,
    PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT,
    PrimitiveActionType.INTERACT_PRIMARY,
}

MINECRAFT_ACTIONS = {
    PrimitiveActionType.COLLECT_BLOCK,
    PrimitiveActionType.CRAFT_ITEM,
    PrimitiveActionType.BUILD_SHELTER,
}


@dataclass(frozen=True)
class ValidationResult:
    status: RecoveryTransition
    reason: str = ""


class Validator:
    """Rejects unsupported, vague, or malformed Plans before execution."""

    def validate_plan(self, plan: Plan) -> ValidationResult:
        if not plan.actions:
            return ValidationResult(RecoveryTransition.ABORT, "plan has no grounded actions")

        for action in plan.actions:
            result = self.validate_action(action)
            if result.status == RecoveryTransition.ABORT:
                return result

        return ValidationResult(RecoveryTransition.CONTINUE)

    def validate_action(self, action: PrimitiveAction) -> ValidationResult:
        if not action.id:
            return ValidationResult(RecoveryTransition.ABORT, "action is missing id")
        if not action.expected_result:
            return ValidationResult(RecoveryTransition.ABORT, f"{action.id} is missing expected_result")
        if action.timeout_ms <= 0:
            return ValidationResult(RecoveryTransition.ABORT, f"{action.id} has invalid timeout_ms")
        if action.adapter == AdapterKind.GENERIC_INPUT and action.type not in GENERIC_ACTIONS:
            return ValidationResult(RecoveryTransition.ABORT, f"{action.type} is not a generic input action")
        if action.adapter == AdapterKind.MINECRAFT and action.type not in MINECRAFT_ACTIONS:
            return ValidationResult(RecoveryTransition.ABORT, f"{action.type} is not a Minecraft adapter action")
        return ValidationResult(RecoveryTransition.CONTINUE)
