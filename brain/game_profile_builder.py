"""Game Profile creation scaffold."""

from models import GameProfile, ResearchNote


class GameProfileBuilder:
    """Builds game profiles from static config or research notes."""

    async def build(self, game_name: str, research_notes: list[ResearchNote] | None = None) -> GameProfile:
        """Create or load a GameProfile.

        TODO(Person B): start with static Minecraft/Minetest profiles, then
        add Exa-backed research only when AgentLoop asks for it.
        """
        raise NotImplementedError("GameProfileBuilder.build is scaffold-only")
