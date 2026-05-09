"""GameProfileBuilder — returns the static Minecraft profile for OmniPlay-MC.

OmniForge's research path is out of scope for this build; the profile is
hardcoded so the curriculum and action agents have stable framing.
"""

from __future__ import annotations

from models import AdapterKind, GameProfile

MINECRAFT_PROFILE = GameProfile(
    game_name="Minecraft",
    genre="open-world survival",
    controls={
        "primary_executor": "mineflayer-jsonrpc-bridge",
        "movement": "bot.pathfinder.goto(goals.GoalNear(x,y,z,n))",
        "mining": "bot.collectBlock.collect(block) or bot.dig(block)",
        "crafting": "bot.craft(recipe, count, craftingTable)",
        "tool_select": "bot.tool.equipForBlock(block)",
        "chat": "bot.chat('...')",
    },
    core_mechanics=[
        "Wood gathering with bare hands or axe",
        "Crafting bench expands the 3x3 grid",
        "Pickaxe tier gates which blocks you can mine (wood -> stone -> iron -> ...)",
        "Hostile mobs spawn in dark areas; safe shelter is critical at night",
        "Hunger depletes from movement; eat food to maintain saturation",
    ],
    early_game_objectives=[
        "Punch a tree to gather oak_log",
        "Craft planks then a crafting_table",
        "Craft a wooden_pickaxe from planks + sticks",
        "Mine cobblestone to upgrade to a stone_pickaxe",
        "Build a small shelter and sleep through the night",
    ],
    benchmark_goals=["survive_first_night", "craft_stone_pickaxe", "build_dirt_shelter"],
    adapter_hints=[AdapterKind.MINECRAFT],
    source="static",
    confidence=1.0,
)


class GameProfileBuilder:
    def get(self, game: str = "minecraft") -> GameProfile:
        if game.lower() != "minecraft":
            raise ValueError(f"OmniPlay-MC only supports minecraft; got {game}")
        return MINECRAFT_PROFILE


__all__ = ["GameProfileBuilder", "MINECRAFT_PROFILE"]
