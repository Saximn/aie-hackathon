"""Decomposes a user-supplied task into atomic sub-tasks before handing to the agent loop."""
import re
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llm_client import LLMClient

LOG = logging.getLogger(__name__)

_ATOMIC_PATTERNS = [
    r"collect \d+",
    r"mine \d+",
    r"craft \d+",
    r"kill \d+",
    r"(go to|walk to|move to)",
    r"dig \d+",
    r"place \d+",
    r"equip ",
    r"eat ",
]

_SYSTEM_PROMPT = (
    "You are a Minecraft task planner. Break the given task into at most 5 simple, atomic sub-tasks. "
    "Each sub-task should be a single action a Minecraft bot can do. "
    "Return ONLY a numbered list, one per line, no explanation."
)


class TaskDecomposer:
    def __init__(self, llm: "LLMClient | None" = None) -> None:
        self._llm = llm

    def is_atomic(self, task: str) -> bool:
        t = task.strip().lower()
        return any(re.search(p, t) for p in _ATOMIC_PATTERNS)

    def decompose(self, task: str) -> list[str]:
        if self.is_atomic(task):
            LOG.debug("task_decomposer: task is already atomic, skipping LLM")
            return [task]
        if self._llm is None:
            LOG.debug("task_decomposer: no LLM available, returning task as-is")
            return [task]
        try:
            response = self._llm.complete(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": f"Task: {task}"},
                ],
                max_tokens=200,
            )
            lines = [l.strip() for l in response.strip().splitlines() if l.strip()]
            # strip leading "1. ", "2. ", etc.
            sub_tasks = [re.sub(r"^\d+\.\s*", "", l) for l in lines if l]
            return sub_tasks[:5] if sub_tasks else [task]
        except Exception as exc:
            LOG.warning("task_decomposer: LLM decomposition failed (%s), using original task", exc)
            return [task]


__all__ = ["TaskDecomposer"]
