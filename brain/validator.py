"""Plan and action validation rules."""

from dataclasses import dataclass
from typing import Any, Callable

from models import Plan, PrimitiveAction, PrimitiveActionType, RecoveryTransition


@dataclass(frozen=True)
class ValidationResult:
    status: RecoveryTransition
    reason: str = ""


class Validator:
    """Rejects unsupported, vague, or malformed Plans before execution."""

    def validate_plan(self, plan: Plan) -> ValidationResult:
        if not plan.actions:
            return ValidationResult(
                status=RecoveryTransition.REPLAN,
                reason="plan must include at least one action",
            )

        seen_ids: set[str] = set()
        for action in plan.actions:
            if action.id in seen_ids:
                return ValidationResult(
                    status=RecoveryTransition.REPLAN,
                    reason=f"duplicate action id: {action.id}",
                )
            seen_ids.add(action.id)

            result = self.validate_action(action)
            if result.status != RecoveryTransition.CONTINUE:
                return result

        return ValidationResult(status=RecoveryTransition.CONTINUE)

    def validate_action(self, action: PrimitiveAction) -> ValidationResult:
        required = _ACTION_REQUIREMENTS.get(action.type)
        if required is None:
            return ValidationResult(
                status=RecoveryTransition.REPLAN,
                reason=f"{action.type} is not configured for validation",
            )

        missing = [name for name, predicate in required if not predicate(action.args.get(name))]
        if missing:
            return ValidationResult(
                status=RecoveryTransition.REPLAN,
                reason=f"{action.type} requires valid args: {', '.join(missing)}",
            )

        return ValidationResult(status=RecoveryTransition.CONTINUE)


def _present(value: Any) -> bool:
    return value is not None and value != ""


def _number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _positive_number(value: Any) -> bool:
    return _number(value) and value > 0


ArgRule = tuple[str, Callable[[Any], bool]]

_ACTION_REQUIREMENTS: dict[PrimitiveActionType, tuple[ArgRule, ...]] = {
    PrimitiveActionType.PRESS_KEY: (("key", _present),),
    PrimitiveActionType.HOLD_KEY: (("key", _present), ("duration_ms", _positive_number)),
    PrimitiveActionType.MOVE_MOUSE: (("dx", _number), ("dy", _number)),
    PrimitiveActionType.CLICK: (("button", _present),),
    PrimitiveActionType.WAIT: (("duration_ms", _positive_number),),
    PrimitiveActionType.OPEN_MENU: (),
    PrimitiveActionType.SELECT_HOTBAR_SLOT: (("slot", lambda value: isinstance(value, int) and 1 <= value <= 9),),
    PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT: (("object", _present),),
    PrimitiveActionType.INTERACT_PRIMARY: (),
    PrimitiveActionType.COLLECT_BLOCK: (("block", _present),),
    PrimitiveActionType.CRAFT_ITEM: (("item", _present),),
    PrimitiveActionType.BUILD_SHELTER: (("material", _present),),
}
