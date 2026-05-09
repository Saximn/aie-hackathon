"""Vendored, langchain-stripped Voyager agents adapted for GPT-5.5.

This package implements the four Voyager components used by the OmniPlay-MC
AgentLoop:

- `curriculum.CurriculumAgent`: proposes the next task given recent progress.
- `action.ActionAgent`: generates an async JS body that the Mineflayer bridge
  evaluates to attempt the task.
- `critic.CriticAgent`: judges whether the task succeeded after execution.
- `skill.SkillManager`: stores reusable code-as-policy skills with vector
  retrieval over OpenAI embeddings.

All agents use the shared `LLMClient` (Responses API + Structured Outputs);
prompt templates live as plain f-strings in `prompts/`.
"""

from .action import ActionAgent, ActionResult
from .critic import CriticAgent, CriticVerdict
from .curriculum import CurriculumAgent, CurriculumProposal
from .skill import RetrievedSkill, SkillManager, SkillRecord

__all__ = [
    "ActionAgent",
    "ActionResult",
    "CriticAgent",
    "CriticVerdict",
    "CurriculumAgent",
    "CurriculumProposal",
    "RetrievedSkill",
    "SkillManager",
    "SkillRecord",
]
