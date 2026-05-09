"""SkillBuilder — turns a successful action into a SkillRecord and persists it."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from voyager_agents import ActionResult, SkillManager
from voyager_agents.skill import SkillRecord

LOG = logging.getLogger("omniplay.skill_builder")


class SkillBuilder:
    def __init__(self, *, skill_manager: SkillManager) -> None:
        self.skill_manager = skill_manager

    def build(self, *, task: str, action: ActionResult) -> SkillRecord:
        name = _normalize_name(action.name) or _name_from_task(task)
        return SkillRecord(
            name=name,
            goal=task,
            code=action.code,
            description=action.explain or task,
            version=1,
            tags=[],
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    async def store(self, record: SkillRecord) -> SkillRecord:
        return self.skill_manager.upsert(record)


_SAFE = re.compile(r"[^a-z0-9_]+")


def _normalize_name(name: str) -> str:
    name = name.strip().lower().replace(" ", "_")
    name = _SAFE.sub("_", name).strip("_")
    return name


def _name_from_task(task: str) -> str:
    return _normalize_name(task) or "skill"


__all__ = ["SkillBuilder"]
