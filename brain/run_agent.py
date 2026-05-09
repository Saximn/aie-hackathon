"""OmniPlay-MC CLI entrypoint.

Boots the Mineflayer bridge subprocess, hydrates the skill library from
Convex (or local fallback) into Chroma, then runs the AgentLoop on either:

    python -m run_agent --task "chop a tree and collect wood"

or the demo curriculum:

    python -m run_agent --demo

Press Ctrl+C to tear everything down cleanly.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent_loop import AgentLoop
from bot_client import BotClient
from diagnoser import Diagnoser
from event_bus import default_bus
from memory_store import MemoryStore
from voice import Narrator
from voyager_agents import SkillManager

LOG = logging.getLogger("omniplay.run_agent")

DEMO_CURRICULUM = [
    "chop a tree and collect 4 oak_log",
    "craft 4 oak_planks from oak_log",
    "craft 1 crafting_table",
    "craft 4 stick from oak_planks",
    "place crafting_table and craft 1 wooden_pickaxe",
    "mine 4 cobblestone with the wooden_pickaxe",
    "craft 1 stone_pickaxe at the crafting_table",
    "build a small dirt shelter around the bot using nearby dirt blocks",
    "sleep through the night by placing and using a bed if available",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="run_agent", description="OmniPlay-MC AgentLoop entrypoint.")
    parser.add_argument("--task", help="Single task to run; bypasses curriculum agent.")
    parser.add_argument("--demo", action="store_true", help="Run the canned demo curriculum.")
    parser.add_argument("--curriculum", action="store_true", help="Use the GPT-5.5 curriculum agent for tasks.")
    parser.add_argument("--max-cycles", type=int, default=int(os.getenv("MAX_CYCLES", "50")))
    parser.add_argument("--host", default=os.getenv("MINECRAFT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MINECRAFT_PORT", "25565")))
    parser.add_argument("--username", default=os.getenv("MINECRAFT_USERNAME", "Voyager"))
    parser.add_argument("--mc-version", default=os.getenv("MINECRAFT_VERSION", "1.20.4"))
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    return parser.parse_args()


def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )


async def _amain(args: argparse.Namespace) -> int:
    skill_manager = SkillManager()
    memory = MemoryStore(skill_manager=skill_manager)
    hydrated = await memory.hydrate_skills_into_chroma()
    LOG.info("hydrated %d skills from %s", hydrated, "convex" if memory.using_convex else "local")
    LOG.info("chroma skill count at boot: %d", skill_manager.count())

    bot_client = BotClient()
    await bot_client.start()
    try:
        await bot_client.connect(host=args.host, port=args.port, username=args.username, version=args.mc_version)
        LOG.info("mineflayer connected to %s:%s as %s", args.host, args.port, args.username)
    except Exception as exc:
        LOG.error("mineflayer connect failed: %s", exc)
        await bot_client.stop()
        return 2

    narrator = Narrator(memory=memory)
    narrator.attach_loop(asyncio.get_running_loop())
    if narrator.enabled:
        LOG.info("narrator enabled (voice %s)", narrator.voice_id)
    else:
        LOG.info("narrator disabled (no ELEVENLABS_API_KEY)")

    loop = AgentLoop(
        bot_client=bot_client,
        skill_manager=skill_manager,
        memory=memory,
        event_bus=default_bus(),
        narrator=narrator,
        diagnoser=Diagnoser(memory=memory),
    )

    task_queue: list[str]
    use_curriculum = False
    if args.task:
        task_queue = [args.task]
    elif args.demo:
        task_queue = list(DEMO_CURRICULUM)
    elif args.curriculum:
        task_queue = []
        use_curriculum = True
    else:
        task_queue = ["chop a tree and collect 1 oak_log"]

    stop_event = asyncio.Event()

    def _on_signal(*_: object) -> None:
        LOG.info("signal received; stopping after current cycle")
        stop_event.set()

    if sys.platform != "win32":
        running_loop = asyncio.get_running_loop()
        for sig_name in ("SIGINT", "SIGTERM"):
            sig = getattr(signal, sig_name, None)
            if sig is not None:
                running_loop.add_signal_handler(sig, _on_signal)

    outcome = "error"
    try:
        result = await loop.run_episode(
            task_queue=task_queue,
            max_cycles=args.max_cycles,
            use_curriculum=use_curriculum,
        )
        outcome = "completed"
    finally:
        narrator.shutdown()
        try:
            await memory.finish_episode(outcome=outcome)
        except Exception as exc:
            LOG.warning("finish_episode failed: %s", exc)
        await bot_client.stop()
    LOG.info("episode done: %s", result)
    return 0


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    args = _parse_args()
    _configure_logging(args.log_level)
    try:
        return asyncio.run(_amain(args))
    except KeyboardInterrupt:
        LOG.info("interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
