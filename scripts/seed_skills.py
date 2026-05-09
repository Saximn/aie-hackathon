"""Pre-seed Chroma + Convex with hand-tuned baseline skills for the demo.

Use this before recording the demo if the agent has never run successfully on
the local Minecraft world. The seeded skills are copy-paste safe Voyager-style
JS bodies that GPT-5.5 will retrieve, adapt, or simply replay.

Run from the repo root with the brain venv active:

    python scripts/seed_skills.py

If `OPENAI_API_KEY` is set the seeds get embedded via `text-embedding-3-small`;
otherwise we fall back to a deterministic stub embedder so the script still
populates the local store.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "brain"))

LOG = logging.getLogger("omniplay.seed")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


SEEDS = [
    {
        "name": "chop_oak_log",
        "goal": "Chop one oak tree and collect at least 1 oak_log.",
        "description": "Find the nearest oak_log block, walk to it, and dig until at least one is in inventory.",
        "code": """
const oakBlock = bot.findBlock({
  matching: mcData.blocksByName.oak_log.id,
  maxDistance: 64,
});
if (!oakBlock) throw new Error('no oak_log within 64 blocks');
await bot.pathfinder.goto(new goals.GoalGetToBlock(oakBlock.position.x, oakBlock.position.y, oakBlock.position.z));
await bot.collectBlock.collect(oakBlock);
const have = (bot.inventory.items().find((i) => i.name === 'oak_log') || { count: 0 }).count;
if (have < 1) throw new Error(`failed to collect oak_log; inventory has ${have}`);
return `collected ${have} oak_log`;
""".strip(),
    },
    {
        "name": "craft_oak_planks_from_log",
        "goal": "Craft 4 oak_planks from any oak_log in the inventory.",
        "description": "Use bot.craft on the oak_planks recipe; no crafting table required.",
        "code": """
const planksItem = mcData.itemsByName.oak_planks;
const recipes = bot.recipesFor(planksItem.id, null, 1, null);
if (!recipes.length) throw new Error('no oak_planks recipe available; need oak_log first');
await bot.craft(recipes[0], 1, null);
const have = (bot.inventory.items().find((i) => i.name === 'oak_planks') || { count: 0 }).count;
return `oak_planks=${have}`;
""".strip(),
    },
    {
        "name": "craft_crafting_table",
        "goal": "Craft 1 crafting_table from oak_planks.",
        "description": "Plain bench craft; no table required.",
        "code": """
const tableItem = mcData.itemsByName.crafting_table;
const recipes = bot.recipesFor(tableItem.id, null, 1, null);
if (!recipes.length) throw new Error('no crafting_table recipe (need 4 planks)');
await bot.craft(recipes[0], 1, null);
const have = (bot.inventory.items().find((i) => i.name === 'crafting_table') || { count: 0 }).count;
return `crafting_table=${have}`;
""".strip(),
    },
    {
        "name": "place_crafting_table_nearby",
        "goal": "Place a crafting_table on a flat block within reach.",
        "description": "Find a solid block under the bot and place the carried crafting_table on top so subsequent crafts can use it.",
        "code": """
const tableItem = bot.inventory.items().find((i) => i.name === 'crafting_table');
if (!tableItem) throw new Error('crafting_table not in inventory');
await bot.equip(tableItem, 'hand');
const refBlock = bot.blockAt(bot.entity.position.offset(0, -1, 0));
if (!refBlock) throw new Error('no ground beneath bot to place against');
await bot.placeBlock(refBlock, new Vec3(0, 1, 0));
return 'crafting_table placed';
""".strip(),
    },
    {
        "name": "find_and_mine_cobblestone",
        "goal": "Mine at least 1 cobblestone using a wooden_pickaxe.",
        "description": "Equip the wooden_pickaxe, find nearby stone, walk to it, and dig.",
        "code": """
const pick = bot.inventory.items().find((i) => i.name === 'wooden_pickaxe' || i.name === 'stone_pickaxe');
if (!pick) throw new Error('no pickaxe equipped to mine cobblestone');
await bot.equip(pick, 'hand');
const stone = bot.findBlock({ matching: mcData.blocksByName.stone.id, maxDistance: 32 });
if (!stone) throw new Error('no stone within 32 blocks');
await bot.pathfinder.goto(new goals.GoalGetToBlock(stone.position.x, stone.position.y, stone.position.z));
await bot.dig(stone);
const have = (bot.inventory.items().find((i) => i.name === 'cobblestone') || { count: 0 }).count;
if (have < 1) throw new Error('did not collect cobblestone');
return `cobblestone=${have}`;
""".strip(),
    },
]


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    have_key = bool(os.getenv("OPENAI_API_KEY"))
    if not have_key:
        os.environ["OPENAI_API_KEY"] = "sk-seed-only"

    from voyager_agents.skill import SkillManager, SkillRecord

    if not have_key:
        from llm_client import LLMClient

        class _StubLLM(LLMClient):
            def __init__(self):
                self.embed_model = "stub"

            def embed(self, texts):
                return [[((hash(t) >> i) & 1) * 0.1 for i in range(8)] for t in texts]

        sm = SkillManager(llm=_StubLLM())
        LOG.info("OPENAI_API_KEY not set — seeding with stub embeddings (retrieval will degrade)")
    else:
        sm = SkillManager()

    from memory_store import MemoryStore

    memory = MemoryStore(skill_manager=sm, episode_id="seeded")
    await memory.start_episode(task="seed_skills")

    for seed in SEEDS:
        record = SkillRecord(
            name=seed["name"],
            goal=seed["goal"],
            code=seed["code"],
            description=seed["description"],
            version=1,
            tags=["seed"],
            created_at=_now(),
        )
        sm.upsert(record)
        await memory.upsert_skill(record)
        LOG.info("seeded %s", record.name)

    LOG.info("done; chroma now has %d skills", sm.count())
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
