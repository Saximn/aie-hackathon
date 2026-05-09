"""Game Profile creation."""

from models import GameProfile, ResearchNote
from models import AdapterKind


class GameProfileBuilder:
    """Builds game profiles from static config or research notes."""

    async def build(self, game_name: str, research_notes: list[ResearchNote] | None = None) -> GameProfile:
        """Create a deterministic Game Profile for planning.

        Static demo profiles are trusted defaults. Research Notes can improve
        low-confidence fallback profiles, but they do not overwrite static
        Minecraft/Minetest knowledge.
        """
        normalized_name = _normalize_game_name(game_name)
        notes = research_notes or []
        static_profile = _STATIC_PROFILES.get(normalized_name)

        if static_profile is not None:
            profile = static_profile.model_copy(deep=True)
            return _append_research_context(profile, notes)

        return _profile_from_research(normalized_name, notes)


def _normalize_game_name(game_name: str) -> str:
    normalized = " ".join(game_name.strip().lower().replace("_", " ").replace("-", " ").split())
    aliases = {
        "mine test": "minetest",
        "mine craft": "minecraft",
    }
    return aliases.get(normalized, normalized or "unknown")


def _append_research_context(profile: GameProfile, notes: list[ResearchNote]) -> GameProfile:
    """Preserve trusted static fields while retaining useful researched context."""
    if not notes:
        return profile

    additions = _research_bullets(notes)
    for addition in additions:
        if addition not in profile.core_mechanics:
            profile.core_mechanics.append(addition)
    return profile


def _profile_from_research(game_name: str, notes: list[ResearchNote]) -> GameProfile:
    if not notes:
        return GameProfile(
            game_name=game_name,
            genre="unknown",
            source="fallback",
            confidence=0.15,
        )

    confidence = max(note.confidence for note in notes)
    return GameProfile(
        game_name=game_name,
        genre=_guess_genre(notes),
        controls=_guess_controls(notes),
        core_mechanics=_research_bullets(notes),
        early_game_objectives=_research_objectives(notes),
        benchmark_goals=[],
        adapter_hints=[AdapterKind.GENERIC_INPUT],
        source="researched",
        confidence=min(0.75, max(0.25, confidence)),
    )


def _research_bullets(notes: list[ResearchNote]) -> list[str]:
    bullets: list[str] = []
    for note in notes:
        for line in note.summary.splitlines():
            cleaned = line.strip(" -\t")
            if cleaned and cleaned not in bullets:
                bullets.append(cleaned)

    if not bullets:
        bullets = [note.summary.strip() for note in notes if note.summary.strip()]

    return bullets[:8]


def _research_objectives(notes: list[ResearchNote]) -> list[str]:
    objectives: list[str] = []
    for bullet in _research_bullets(notes):
        lowered = bullet.lower()
        if any(keyword in lowered for keyword in ("first", "early", "start", "survive", "craft", "collect")):
            objectives.append(bullet)
    return objectives[:5]


def _guess_controls(notes: list[ResearchNote]) -> dict[str, str]:
    text = "\n".join(note.summary.lower() for note in notes)
    if any(keyword in text for keyword in ("wasd", "keyboard", "mouse")):
        return {
            "move": "WASD",
            "look": "mouse",
            "interact": "right_click",
            "primary_action": "left_click",
        }
    return {}


def _guess_genre(notes: list[ResearchNote]) -> str:
    text = "\n".join(note.summary.lower() for note in notes)
    if "survival" in text and "sandbox" in text:
        return "sandbox survival"
    if "survival" in text:
        return "survival"
    if "sandbox" in text:
        return "sandbox"
    return "unknown"


_STATIC_PROFILES: dict[str, GameProfile] = {
    "minecraft": GameProfile(
        game_name="minecraft",
        genre="sandbox survival",
        controls={
            "move": "WASD",
            "look": "mouse",
            "jump": "space",
            "sneak": "left_shift",
            "inventory": "e",
            "primary_action": "left_click",
            "interact": "right_click",
            "hotbar": "number_keys_1_to_9",
        },
        core_mechanics=[
            "Break blocks to gather resources.",
            "Craft tools and shelter from gathered resources.",
            "Manage hunger, health, light, and hostile mobs.",
            "Night increases combat risk for an exposed player.",
        ],
        early_game_objectives=[
            "Collect wood from nearby trees.",
            "Craft planks, sticks, and basic tools.",
            "Gather food or identify a safe food source.",
            "Build or find shelter before night.",
        ],
        benchmark_goals=["survive_first_night"],
        adapter_hints=[AdapterKind.GENERIC_INPUT, AdapterKind.MINECRAFT],
        source="static",
        confidence=0.95,
    ),
    "minetest": GameProfile(
        game_name="minetest",
        genre="sandbox survival",
        controls={
            "move": "WASD",
            "look": "mouse",
            "jump": "space",
            "sneak": "left_shift",
            "inventory": "i",
            "primary_action": "left_click",
            "interact": "right_click",
            "hotbar": "number_keys_1_to_9",
        },
        core_mechanics=[
            "Dig nodes to collect resources.",
            "Craft simple tools and building materials.",
            "Use light and shelter to reduce survival risk.",
            "Game rules vary by installed game and mods.",
        ],
        early_game_objectives=[
            "Collect wood or other nearby starter resources.",
            "Craft basic tools if recipes are available.",
            "Find or build a simple safe shelter.",
            "Avoid risky exploration until the area is understood.",
        ],
        benchmark_goals=["survive_first_night"],
        adapter_hints=[AdapterKind.GENERIC_INPUT],
        source="static",
        confidence=0.85,
    ),
}
