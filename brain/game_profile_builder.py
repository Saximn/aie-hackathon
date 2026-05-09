"""Game Profile creation scaffold for OmniForge."""

from __future__ import annotations

from models import AdapterKind, GameProfile, ResearchNote


STATIC_PROFILES: dict[str, GameProfile] = {
    "minecraft": GameProfile(
        game_name="Minecraft",
        genre="open-world survival sandbox",
        controls={
            "moveForward": "W",
            "moveLeft": "A",
            "moveBack": "S",
            "moveRight": "D",
            "jump": "Space",
            "attack": "LeftClick",
            "use": "RightClick",
            "inventory": "E",
            "hotbar1": "1",
            "hotbar2": "2",
            "hotbar3": "3",
        },
        core_mechanics=[
            "gather resources",
            "craft tools",
            "build shelter",
            "avoid hostile mobs",
            "manage hunger and health",
        ],
        early_game_objectives=[
            "collect wood",
            "craft basic tools",
            "build a basic shelter",
            "find food",
            "avoid danger after dark",
        ],
        adapter_hints=[AdapterKind.GENERIC_INPUT, AdapterKind.MINECRAFT],
    ),
    "minetest": GameProfile(
        game_name="Minetest",
        genre="open-world survival sandbox",
        controls={
            "moveForward": "W",
            "moveLeft": "A",
            "moveBack": "S",
            "moveRight": "D",
            "jump": "Space",
            "dig": "LeftClick",
            "place": "RightClick",
            "inventory": "I",
        },
        core_mechanics=[
            "gather resources",
            "craft basic items",
            "build shelter",
            "manage danger from environment and mobs when enabled",
        ],
        early_game_objectives=[
            "collect wood",
            "craft starter items",
            "build a basic shelter",
            "stay safe after dark",
        ],
        adapter_hints=[AdapterKind.GENERIC_INPUT],
    ),
}


class GameProfileBuilder:
    """Builds game-agnostic profiles from static config or research notes."""

    async def build(self, game_name: str, research_notes: list[ResearchNote] | None = None) -> GameProfile:
        """Return a GameProfile for the requested game.

        TODO(Person B): call Researcher/Exa only when the AgentLoop decides a
        new or incomplete profile needs external knowledge.
        """
        normalized = game_name.strip().lower()
        if normalized in STATIC_PROFILES:
            return STATIC_PROFILES[normalized]

        return GameProfile(
            game_name=game_name,
            genre="unknown open-world game",
            controls={},
            core_mechanics=[],
            early_game_objectives=[],
            source="researched" if research_notes else "static",
            confidence=0.2,
        )
