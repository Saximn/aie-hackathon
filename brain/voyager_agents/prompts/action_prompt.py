"""Action-agent prompts for OmniPlay-MC.

The action agent emits an async JS body that the Mineflayer bridge evaluates.
The body has access to: bot, mcData, Vec3, goals, Movements.
"""

from __future__ import annotations

from typing import Any

ACTION_SYSTEM = """You are the Action Agent for Voyager, an autonomous Minecraft player.

You are given:
- a single task to complete (e.g. "Mine 3 oak_log"),
- the current World Snapshot (inventory, nearby blocks, entities, position, biome, time, health, hunger),
- a list of relevant skills retrieved from memory,
- optionally, the last attempt's error if you are retrying.

You must produce ONE async JavaScript body that, when wrapped in
`(async (bot, mcData, Vec3, goals, Movements) => { <YOUR CODE> })()`,
attempts the task using `mineflayer-pathfinder`, `mineflayer-collectblock`,
and `mineflayer-tool` (already loaded as plugins).

Hard rules:
- The body MUST `return` a short success/failure description string at the end.
- The body MUST throw a descriptive `Error` if it cannot make progress; do not swallow errors.
- Do NOT use `require`, `import`, file I/O, network calls, or `process.*`.
- Do NOT define functions outside the body or rely on global state from prior runs.
- Only use named primitives the snippet receives as arguments.
- Use `bot.collectBlock.collect`, `bot.tool.equipForBlock`, `bot.pathfinder.goto(new goals.GoalNear(x, y, z, n))`, etc.
- Always check `bot.findBlock`, `bot.findBlocks`, or `bot.entity.position` BEFORE moving.
- When crafting, find or place a crafting table first; recipe = `bot.recipesFor(mcData.itemsByName.<name>.id, null, 1, craftingTable)[0]`.
- Keep total wall-clock under 60 seconds.

You MAY include short single-line `// comments` for the human reader. No long comments.
"""


def action_messages(
    *,
    task: str,
    rationale: str,
    snapshot_text: str,
    retrieved_skills: list[dict[str, str]],
    last_error: str | None,
    last_code: str | None,
) -> list[dict[str, Any]]:
    skills_block = (
        "\n".join(
            f"### {s['name']}\n# goal: {s.get('goal', '')}\n```js\n{s['code']}\n```"
            for s in retrieved_skills[:3]
        )
        or "(no skills retrieved)"
    )
    user_parts = [
        f"Task: {task}",
        f"Why: {rationale}",
        "",
        "World snapshot:",
        snapshot_text,
        "",
        "Retrieved skills (use as inspiration; do NOT call by name, copy the code you need):",
        skills_block,
    ]
    if last_error:
        user_parts.append("")
        user_parts.append(f"Previous attempt failed with: {last_error}")
    if last_code:
        user_parts.append("Previous code:")
        user_parts.append("```js")
        user_parts.append(last_code[:4000])
        user_parts.append("```")
        user_parts.append("Diagnose the failure and produce a corrected body. Do not repeat the same mistake.")
    user_parts.append("")
    user_parts.append(
        "Reply with JSON: { explain: short why-this-plan, plan: ordered steps as strings, "
        "code: the JS body, name: snake_case skill name to save IF this works }"
    )
    return [
        {"role": "system", "content": ACTION_SYSTEM},
        {"role": "user", "content": "\n".join(user_parts)},
    ]
