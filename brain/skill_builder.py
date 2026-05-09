"""Skill creation scaffold."""

from models import Plan, Skill


class SkillBuilder:
    """Creates versioned structured Skills from plans, coaching, and research."""

    def from_plan(self, plan: Plan) -> Skill:
        raise NotImplementedError("SkillBuilder.from_plan is scaffold-only")

    def promote_after_success(self, skill: Skill) -> Skill:
        raise NotImplementedError("SkillBuilder.promote_after_success is scaffold-only")
