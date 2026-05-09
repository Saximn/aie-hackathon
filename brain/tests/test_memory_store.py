from __future__ import annotations

import sys
from asyncio import run
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory_store import MemoryStore
from models import AgentEvent, AgentEventType, Skill


class FakeMemories:
    def __init__(self) -> None:
        self.add_calls = []
        self.search_calls = []

    def add(self, **kwargs):
        self.add_calls.append(kwargs)
        return object()

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return type("SearchResponse", (), {"answer": "remembered context", "documents": []})()


class FakeClient:
    def __init__(self) -> None:
        self.memories = FakeMemories()


def memory_store_with_fake_client() -> tuple[MemoryStore, FakeClient]:
    client = FakeClient()
    store = MemoryStore(user_id="test-user")
    store._client = client
    return store, client


def test_append_event_adds_searchable_memory() -> None:
    store, client = memory_store_with_fake_client()
    event = AgentEvent(
        id="evt-1",
        timestamp="2026-05-09T00:00:00Z",
        event_type=AgentEventType.GOAL_RECEIVED,
        cycle=3,
        data={"goal": "collect wood"},
    )

    run(store.append_event(event))

    call = client.memories.add_calls[0]
    assert call["resource_id"] == "event:evt-1"
    assert call["collection"] == "omniforge-agent-memory"
    assert call["metadata"]["kind"] == "agent_event"
    assert call["metadata"]["event_type"] == "goal_received"
    assert "collect wood" in call["text"]


def test_upsert_skill_adds_procedural_memory() -> None:
    store, client = memory_store_with_fake_client()
    skill = Skill(name="gather_wood", goal="Collect wood safely")

    run(store.upsert_skill(skill))

    call = client.memories.add_calls[0]
    assert call["resource_id"] == "skill:gather_wood:v1"
    assert call["collection"] == "omniforge-agent-memory"
    assert call["metadata"]["kind"] == "skill"
    assert call["metadata"]["skill_name"] == "gather_wood"


def test_context_queries_hyperspell_collection() -> None:
    store, client = memory_store_with_fake_client()

    context = run(store.context("what should I do next?"))

    assert context == "remembered context"
    call = client.memories.search_calls[0]
    assert call["query"] == "what should I do next?"
    assert call["answer"] is True
    assert call["max_results"] == 8
    assert call["sources"] == ["vault"]
