"""Skill building scaffold."""

from models import Skill


class SkillBuilder:
    """Converts verified or researched guidance into structured Skills."""

    def from_research(self, name: str, goal: str) -> Skill:
        # TODO(Person B): derive action templates, criteria, source, and confidence.
        return Skill(name=name, goal=goal)
