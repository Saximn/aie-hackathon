"""Skill creation and promotion rules."""

import re
from datetime import UTC, datetime

from models import Plan, Skill, SkillActionTemplate, SkillStatus


class SkillBuilder:
    """Creates versioned structured Skills from plans, coaching, and research."""

    def from_plan(self, plan: Plan) -> Skill:
        return Skill(
            name=_skill_name(plan.goal),
            goal=plan.goal,
            ordered_actions=[
                SkillActionTemplate(
                    type=action.type,
                    args_template=action.args,
                    adapter=action.adapter,
                )
                for action in plan.actions
            ],
            success_criteria=[_success_criterion(action.expected_result) for action in plan.actions],
        )

    def promote_after_success(self, skill: Skill) -> Skill:
        return skill.model_copy(
            update={
                "version": skill.version + 1,
                "status": SkillStatus.VERIFIED,
                "confidence": min(max(skill.confidence, 0.7) + 0.1, 1.0),
                "last_verified_at": datetime.now(UTC).isoformat(),
            },
            deep=True,
        )


def _skill_name(goal: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", goal.lower()).strip("_")
    return name or "unnamed_skill"


def _success_criterion(expected_result: dict[str, object]) -> str:
    if not expected_result:
        return "action completed"

    key, value = next(iter(expected_result.items()))
    return f"{key}: {value}"
