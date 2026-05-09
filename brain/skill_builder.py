"""Skill creation scaffold."""

from __future__ import annotations

from models import Plan, Skill, SkillActionTemplate, SkillFailureMode, SkillSource, FailureType


class SkillBuilder:
    """Creates versioned structured Skills from plans, coaching, and research."""

    def from_plan(self, plan: Plan, source: str = "learned") -> Skill:
        normalized_goal = plan.goal.strip().lower().replace(" ", "_")
        action_templates = [
            SkillActionTemplate(
                type=action.type,
                args_template=action.args,
                adapter=action.adapter,
            )
            for action in plan.actions
        ]

        return Skill(
            name=f"{normalized_goal}_candidate",
            version=1,
            goal=plan.goal,
            preconditions=["World Snapshot matches the same broad situation as the source plan."],
            ordered_actions=action_templates,
            success_criteria=[
                "Verifier reports success for each action in the procedure.",
                "Post-action World Snapshot matches the expected result.",
            ],
            failure_modes=[
                SkillFailureMode(
                    type=FailureType.VISUAL_MISALIGNMENT,
                    repair="Re-observe and recenter the visible target before retrying.",
                )
            ],
            source=SkillSource(source),
            confidence=0.6,
        )
