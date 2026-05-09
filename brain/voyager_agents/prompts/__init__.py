"""Prompt templates for the OmniPlay-MC voyager agents.

Each prompt is a plain f-string producing the system+user message pair handed
to `LLMClient.complete`. Voyager's original GPT-4 framing (long few-shot blocks,
"you are GPT-4" lines, hand-rolled JSON parsing instructions) has been
trimmed: GPT-5.5 with Structured Outputs handles JSON shape natively.
"""

from .action_prompt import action_messages
from .critic_prompt import critic_messages
from .curriculum_prompt import curriculum_messages

__all__ = ["action_messages", "critic_messages", "curriculum_messages"]
