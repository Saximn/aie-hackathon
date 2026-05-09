"""Tests for brain/imagine.py — SkillCardGenerator text fallback."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "brain"))

import os

import pytest

from imagine import SkillCardGenerator


def test_generate_returns_markdown_with_skill_name() -> None:
    card = SkillCardGenerator().generate("mine_wood", "Mines wood logs")
    assert "mine_wood" in card


def test_generate_contains_skill_description() -> None:
    card = SkillCardGenerator().generate("mine_wood", "Mines wood logs")
    assert "Mines wood logs" in card


def test_generate_returns_string() -> None:
    result = SkillCardGenerator().generate("smelt_iron", "Smelts iron ore into ingots")
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_does_not_raise_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Should never raise regardless of environment
    card = SkillCardGenerator().generate("gather_wood", "Gathers wood from nearby trees")
    assert "gather_wood" in card


def test_generate_includes_h2_heading() -> None:
    card = SkillCardGenerator().generate("build_shelter", "Builds a basic shelter")
    assert card.startswith("## Skill: build_shelter")
