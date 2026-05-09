from __future__ import annotations

import json
import sys
from asyncio import run
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory_store import MemoryStore
from models import AdapterKind, GameProfile, ResearchNote
from researcher import Researcher


class FakeProvider:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def search(self, query: str) -> ResearchNote:
        self.queries.append(query)
        return ResearchNote(
            query="provider-specific query",
            summary="  Gather wood before nightfall.  ",
            source_urls=[
                " https://wiki.example/survival ",
                "",
                "https://wiki.example/survival",
                "https://guide.example/first-night",
            ],
            confidence=1.4,
        )


class FailingProvider:
    async def search(self, query: str) -> ResearchNote:
        raise RuntimeError("provider secret token should not leak")


class FakeMemories:
    def __init__(self) -> None:
        self.add_calls = []

    def add(self, **kwargs):
        self.add_calls.append(kwargs)
        return object()


class FakeClient:
    def __init__(self) -> None:
        self.memories = FakeMemories()


class FakeMemoryStore(MemoryStore):
    def __init__(self, client: FakeClient) -> None:
        super().__init__(user_id="test-user")
        self._fake_client = client

    @property
    def client(self) -> FakeClient:
        return self._fake_client


def test_researcher_returns_controlled_low_confidence_note_on_provider_failure() -> None:
    researcher = Researcher(provider=FailingProvider())

    note = run(researcher.research("  craft shelter  "))

    assert note.query == "craft shelter"
    assert note.summary == "Research unavailable."
    assert note.source_urls == []
    assert note.confidence == 0.0


def test_researcher_normalizes_provider_output_into_structured_research_note() -> None:
    provider = FakeProvider()
    researcher = Researcher(provider=provider)

    note = run(researcher.research("  survive   first night  "))

    assert provider.queries == ["survive first night"]
    assert note.query == "survive first night"
    assert note.summary == "Gather wood before nightfall."
    assert note.source_urls == [
        "https://wiki.example/survival",
        "https://guide.example/first-night",
    ]
    assert note.confidence == 1.0


def test_memory_store_persists_research_note_with_safe_metadata() -> None:
    client = FakeClient()
    store = FakeMemoryStore(client)
    note = ResearchNote(
        query="minecraft first night shelter",
        summary="Collect wood, craft basic tools, and build a small shelter.",
        source_urls=["https://wiki.example/survival"],
        confidence=0.8,
    )

    run(store.append_research_note(note))

    call = client.memories.add_calls[0]
    assert call["resource_id"] == "research:minecraft-first-night-shelter"
    assert call["title"] == "Research Note: minecraft first night shelter"
    assert call["metadata"] == {
        "kind": "research_note",
        "query": "minecraft first night shelter",
        "confidence": "0.8",
    }
    assert json.loads(call["text"]) == note.model_dump(mode="json")


def test_memory_store_persists_game_profile_with_safe_metadata() -> None:
    client = FakeClient()
    store = FakeMemoryStore(client)
    profile = GameProfile(
        game_name="Minetest",
        genre="open-world survival sandbox",
        controls={"forward": "W", "inventory": "I"},
        core_mechanics=["collect nodes", "craft tools"],
        early_game_objectives=["collect wood", "make tools"],
        benchmark_goals=["survive_first_night"],
        adapter_hints=[AdapterKind.GENERIC_INPUT],
        source="researched",
        confidence=0.7,
    )

    run(store.upsert_game_profile(profile))

    call = client.memories.add_calls[0]
    assert call["resource_id"] == "game_profile:minetest"
    assert call["title"] == "Game Profile: Minetest"
    assert call["metadata"] == {
        "kind": "game_profile",
        "game_name": "Minetest",
        "source": "researched",
        "confidence": "0.7",
    }
    assert json.loads(call["text"]) == profile.model_dump(mode="json")
