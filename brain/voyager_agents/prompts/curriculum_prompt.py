"""Curriculum-agent prompts for OmniPlay-MC."""

from __future__ import annotations

from typing import Any

CURRICULUM_SYSTEM = """You are the Curriculum Agent for an autonomous Minecraft player named Voyager.
Your job is to propose the single next task that will most efficiently move the
agent toward open-ended Minecraft mastery, taking the player's current
inventory, biome, time of day, health, hunger, completed tasks, and recent
failures into account.

Rules:
- Tasks must be concrete and testable (e.g. "Mine 3 oak_log", "Craft 1 wooden_pickaxe", not "explore").
- Prefer the smallest unit of progress over a multi-step task.
- Never propose tasks the agent already completed (in `completed_tasks`).
- Avoid tasks that the agent recently failed unless the world state has materially changed.
- If the player is in danger (low health, hostile mobs at night), the task must mitigate the danger first.
- Keep the task achievable within ~50 in-game seconds for the action agent.
"""


def curriculum_messages(
    *,
    biome: str | None,
    time_of_day: str,
    health: float | None,
    hunger: float | None,
    inventory: dict[str, int],
    nearby_blocks: list[str],
    nearby_entities: list[str],
    completed_tasks: list[str],
    failed_tasks: list[str],
    user_constraints: str | None = None,
) -> list[dict[str, Any]]:
    user = (
        f"Player state:\n"
        f"- biome: {biome or 'unknown'}\n"
        f"- time_of_day: {time_of_day}\n"
        f"- health: {health}\n"
        f"- hunger: {hunger}\n"
        f"- inventory: {inventory}\n"
        f"- nearby_blocks: {nearby_blocks[:20]}\n"
        f"- nearby_entities: {nearby_entities[:10]}\n"
        f"\n"
        f"Completed tasks ({len(completed_tasks)}): {completed_tasks[-15:]}\n"
        f"Recently failed tasks ({len(failed_tasks)}): {failed_tasks[-5:]}\n"
    )
    if user_constraints:
        user += f"\nUser constraint: {user_constraints}\n"
    user += (
        "\nReturn JSON: { task: short imperative phrase, rationale: 1-sentence justification, "
        "context: { reason_short: e.g. 'has_no_axe' or 'night_no_shelter' } }"
    )
    return [
        {"role": "system", "content": CURRICULUM_SYSTEM},
        {"role": "user", "content": user},
    ]
