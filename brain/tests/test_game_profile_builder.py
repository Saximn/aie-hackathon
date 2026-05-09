from __future__ import annotations

from asyncio import run
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game_profile_builder import GameProfileBuilder
from models import AdapterKind, ResearchNote


def build_profile(game_name: str, notes: list[ResearchNote] | None = None):
    return run(GameProfileBuilder().build(game_name, notes))


def test_builds_deterministic_minecraft_game_profile() -> None:
    profile = build_profile("Minecraft")

    assert profile.game_name == "minecraft"
    assert profile.genre == "sandbox survival"
    assert profile.source == "static"
    assert profile.confidence >= 0.9
    assert profile.controls["move"] == "WASD"
    assert profile.controls["inventory"] == "e"
    assert "survive_first_night" in profile.benchmark_goals
    assert AdapterKind.GENERIC_INPUT in profile.adapter_hints
    assert AdapterKind.MINECRAFT in profile.adapter_hints
    assert any("shelter" in objective.lower() for objective in profile.early_game_objectives)
    assert any("hostile mobs" in mechanic.lower() for mechanic in profile.core_mechanics)


def test_builds_deterministic_minetest_game_profile() -> None:
    profile = build_profile("mine-test")

    assert profile.game_name == "minetest"
    assert profile.genre == "sandbox survival"
    assert profile.source == "static"
    assert profile.confidence >= 0.8
    assert profile.controls["move"] == "WASD"
    assert profile.controls["inventory"] == "i"
    assert "survive_first_night" in profile.benchmark_goals
    assert profile.adapter_hints == [AdapterKind.GENERIC_INPUT]
    assert any("mods" in mechanic.lower() for mechanic in profile.core_mechanics)
    assert any("safe shelter" in objective.lower() for objective in profile.early_game_objectives)


def test_unknown_game_returns_low_confidence_fallback_profile() -> None:
    profile = build_profile("Veloren")

    assert profile.game_name == "veloren"
    assert profile.source == "fallback"
    assert profile.confidence < 0.25
    assert profile.genre == "unknown"
    assert profile.controls == {}
    assert profile.core_mechanics == []
    assert profile.early_game_objectives == []
    assert profile.benchmark_goals == []
    assert profile.adapter_hints == []


def test_research_notes_fill_unknown_game_profile_deterministically() -> None:
    notes = [
        ResearchNote(
            query="veloren early survival controls",
            summary=(
                "- Veloren is an open-world sandbox survival RPG.\n"
                "- Use WASD and mouse for movement and camera control.\n"
                "- Early start: collect food, gather starter materials, and avoid night risk.\n"
                "- Craft basic tools before exploring caves."
            ),
            source_urls=["https://example.test/veloren"],
            confidence=0.68,
        ),
        ResearchNote(
            query="veloren shelter strategy",
            summary="- Early start: collect food, gather starter materials, and avoid night risk.",
            source_urls=["https://example.test/veloren-shelter"],
            confidence=0.52,
        ),
    ]

    first = build_profile("Veloren", notes)
    second = build_profile("Veloren", notes)

    assert first == second
    assert first.game_name == "veloren"
    assert first.source == "researched"
    assert first.confidence == 0.68
    assert first.genre == "sandbox survival"
    assert first.controls["move"] == "WASD"
    assert first.controls["look"] == "mouse"
    assert first.adapter_hints == [AdapterKind.GENERIC_INPUT]
    assert first.core_mechanics == [
        "Veloren is an open-world sandbox survival RPG.",
        "Use WASD and mouse for movement and camera control.",
        "Early start: collect food, gather starter materials, and avoid night risk.",
        "Craft basic tools before exploring caves.",
    ]
    assert first.early_game_objectives == [
        "Early start: collect food, gather starter materials, and avoid night risk.",
        "Craft basic tools before exploring caves.",
    ]


def test_low_confidence_research_does_not_overwrite_static_minecraft_defaults() -> None:
    notes = [
        ResearchNote(
            query="minecraft bad controls",
            summary=(
                "- Minecraft inventory opens with tab.\n"
                "- Ignore shelter and explore at night first.\n"
                "- Use only a game-specific adapter."
            ),
            source_urls=["https://example.test/untrusted"],
            confidence=0.2,
        )
    ]

    profile = build_profile("minecraft", notes)

    assert profile.source == "static"
    assert profile.confidence == 0.95
    assert profile.controls["inventory"] == "e"
    assert profile.adapter_hints == [AdapterKind.GENERIC_INPUT, AdapterKind.MINECRAFT]
    assert "survive_first_night" in profile.benchmark_goals
    assert "Minecraft inventory opens with tab." not in profile.core_mechanics
    assert "Ignore shelter and explore at night first." not in profile.core_mechanics
    assert "Use only a game-specific adapter." not in profile.core_mechanics
    assert profile.early_game_objectives == [
        "Collect wood from nearby trees.",
        "Craft planks, sticks, and basic tools.",
        "Gather food or identify a safe food source.",
        "Build or find shelter before night.",
    ]
