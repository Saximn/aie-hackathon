"""Plan and action validation scaffold."""

from dataclasses import dataclass

from models import Plan, PrimitiveAction, RecoveryTransition


@dataclass(frozen=True)
class ValidationResult:
    status: RecoveryTransition
    reason: str = ""


class Validator:
    """Rejects unsupported, vague, or malformed Plans before execution."""

    def validate_plan(self, plan: Plan) -> ValidationResult:
        raise NotImplementedError("Validator.validate_plan is scaffold-only")

    def validate_action(self, action: PrimitiveAction) -> ValidationResult:
        raise NotImplementedError("Validator.validate_action is scaffold-only")
