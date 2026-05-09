"""Skill creation and promotion rules."""

import re
from datetime import UTC, datetime

from models import (
    FailureType,
    Plan,
    PrimitiveActionType,
    ResearchNote,
    Skill,
    SkillActionTemplate,
    SkillFailureMode,
    SkillSource,
    SkillStatus,
)


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

    def from_guidance(
        self,
        goal: str,
        guidance: ResearchNote | str,
        source: SkillSource = SkillSource.RESEARCHED,
    ) -> Skill:
        """Create a structured candidate Skill from researched or coached guidance."""
        text = guidance.summary if isinstance(guidance, ResearchNote) else guidance
        confidence = guidance.confidence if isinstance(guidance, ResearchNote) else 0.6
        actions = _action_templates_from_guidance(text)
        return Skill(
            name=_skill_name(goal),
            goal=goal,
            preconditions=_preconditions_from_guidance(text),
            ordered_actions=actions,
            success_criteria=_success_criteria_from_guidance(text),
            failure_modes=_failure_modes_from_guidance(text),
            source=source,
            confidence=min(max(confidence, 0.1), 0.8),
            status=SkillStatus.CANDIDATE,
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


def _action_templates_from_guidance(text: str) -> list[SkillActionTemplate]:
    lowered = text.lower()
    actions: list[SkillActionTemplate] = []
    if "wood" in lowered or "tree" in lowered:
        actions.append(
            SkillActionTemplate(
                type=PrimitiveActionType.MOVE_TOWARD_VISIBLE_OBJECT,
                args_template={"object": "tree"},
            )
        )
        actions.append(
            SkillActionTemplate(
                type=PrimitiveActionType.COLLECT_BLOCK,
                args_template={"block": "wood"},
            )
        )
    if "craft" in lowered and ("plank" in lowered or "wood" in lowered):
        actions.append(
            SkillActionTemplate(
                type=PrimitiveActionType.CRAFT_ITEM,
                args_template={"item": "wooden_planks"},
            )
        )
    if "shelter" in lowered:
        actions.append(
            SkillActionTemplate(
                type=PrimitiveActionType.BUILD_SHELTER,
                args_template={"material": "wood"},
            )
        )
    if not actions:
        actions.append(
            SkillActionTemplate(
                type=PrimitiveActionType.WAIT,
                args_template={"duration_ms": 500},
            )
        )
    return actions


def _preconditions_from_guidance(text: str) -> list[str]:
    preconditions = ["Use only validated Primitive Actions."]
    if "night" in text.lower():
        preconditions.append("Prefer action before night or when night risk is manageable.")
    return preconditions


def _success_criteria_from_guidance(text: str) -> list[str]:
    lowered = text.lower()
    criteria: list[str] = []
    if "wood" in lowered:
        criteria.append("inventory_contains: {'wood': 1}")
    if "shelter" in lowered:
        criteria.append("visible_object: shelter")
    return criteria or ["guidance followed without unsafe verification"]


def _failure_modes_from_guidance(text: str) -> list[SkillFailureMode]:
    modes = [
        SkillFailureMode(
            type=FailureType.MISSING_STRATEGY,
            repair="Ask AgentLoop to research or request user coaching.",
        )
    ]
    if "night" in text.lower() or "mob" in text.lower():
        modes.append(
            SkillFailureMode(
                type=FailureType.UNSAFE_STATE,
                repair="Abort or replan away from hostile risk.",
            )
        )
    return modes
