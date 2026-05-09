"""Plan and PrimitiveAction validation scaffold."""

from models import Plan


class Validator:
    """Rejects unsupported, vague, or malformed plans before execution."""

    def validate_plan(self, plan: Plan) -> Plan:
        # TODO(Person B): require grounded actions, expected results, timeouts, and policies.
        return plan
