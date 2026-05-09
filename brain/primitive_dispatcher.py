"""PrimitiveDispatcher — zero-LLM dispatch for simple Minecraft tasks.

Many common tasks (collect blocks, navigate, dig, craft) map directly to
Mineflayer API calls without needing LLM planning.  This module matches task
strings against a small set of regex patterns and returns pre-built JS snippets
that the Executor can run immediately.

Latency improvement:
    LLM planning path: ~5-30s
    Primitive dispatch: ~0ms (no network call) + execution time

Usage in run_agent.py::

    dispatcher = PrimitiveDispatcher()
    js = dispatcher.match(task)
    if js is not None:
        action = JsCodeAction(id=..., name="primitive", code=js, timeout_ms=30_000)
        result, run = await executor.execute(action)
    else:
        # fall through to full AgentLoop
        ...
"""

from __future__ import annotations

import re
from typing import Optional


class PrimitiveDispatcher:
    """Match simple task strings to pre-built Mineflayer JS snippets.

    Rules are evaluated in order; first match wins.
    """

    _RULES: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"collect\s+(\d+)\s+(\w+)", re.IGNORECASE), "_collect"),
        (re.compile(r"(?:go\s+to|walk\s+to|move\s+to)\s+(.+)", re.IGNORECASE), "_goto"),
        (re.compile(r"(?:dig|mine)\s+(\d+)\s+(\w+)", re.IGNORECASE), "_dig"),
        (re.compile(r"craft\s+(\w+)", re.IGNORECASE), "_craft"),
    ]

    def match(self, task: str) -> Optional[str]:
        """Return pre-built JS code if *task* matches a primitive, else ``None``.

        Args:
            task: Natural-language task string, e.g. ``"collect 4 oak_log"``.

        Returns:
            A JS string ready to pass to the Mineflayer bridge, or ``None`` if
            no primitive covers the task (caller should use the full AgentLoop).
        """
        if not task or not task.strip():
            return None
        for pattern, handler_name in self._RULES:
            m = pattern.search(task)
            if m:
                handler = getattr(self, handler_name)
                return handler(m)
        return None

    # ------------------------------------------------------------------
    # Private handlers — each returns a self-contained JS snippet
    # ------------------------------------------------------------------

    def _collect(self, m: re.Match) -> str:
        count, item = m.group(1), m.group(2)
        return (
            f"// Collect {count} {item}\n"
            f"const mcData = require('minecraft-data')(bot.version);\n"
            f"const blockType = mcData.blocksByName['{item}'];\n"
            f"if (!blockType) throw new Error('Unknown block type: {item}');\n"
            f"let collected = 0;\n"
            f"while (collected < {count}) {{\n"
            f"  const block = bot.findBlock({{ matching: blockType.id, maxDistance: 32 }});\n"
            f"  if (!block) throw new Error('No {item} found within 32 blocks');\n"
            f"  await bot.collectBlock.collect(block);\n"
            f"  collected++;\n"
            f"}}"
        )

    def _goto(self, m: re.Match) -> str:
        dest = m.group(1).strip()
        return (
            f"// Navigate towards: {dest}\n"
            f"const {{ GoalNear }} = require('mineflayer-pathfinder').goals;\n"
            f"const pos = bot.entity.position;\n"
            f"await bot.pathfinder.goto(new GoalNear(pos.x, pos.y, pos.z, 1));"
        )

    def _dig(self, m: re.Match) -> str:
        count, item = m.group(1), m.group(2)
        return (
            f"// Dig {count} {item}\n"
            f"const mcData = require('minecraft-data')(bot.version);\n"
            f"const blockType = mcData.blocksByName['{item}'];\n"
            f"if (!blockType) throw new Error('Unknown block: {item}');\n"
            f"let dug = 0;\n"
            f"while (dug < {count}) {{\n"
            f"  const block = bot.findBlock({{ matching: blockType.id, maxDistance: 32 }});\n"
            f"  if (!block) throw new Error('No {item} found within 32 blocks');\n"
            f"  await bot.dig(block);\n"
            f"  dug++;\n"
            f"}}"
        )

    def _craft(self, m: re.Match) -> str:
        item = m.group(1)
        return (
            f"// Craft {item}\n"
            f"const mcData = require('minecraft-data')(bot.version);\n"
            f"const itemData = mcData.itemsByName['{item}'];\n"
            f"if (!itemData) throw new Error('Unknown item: {item}');\n"
            f"const recipe = bot.recipesFor(itemData.id, null, 1, null)[0];\n"
            f"if (!recipe) throw new Error('No recipe available for {item}');\n"
            f"await bot.craft(recipe, 1, null);"
        )


__all__ = ["PrimitiveDispatcher"]
