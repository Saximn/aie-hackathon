"""Memory store backed by Hyperspell."""

from __future__ import annotations

import json
from typing import Any

from config import settings
from models import AgentEvent, GameProfile, ResearchNote, Skill


class MemoryStore:
    """Persists events, failures, user preferences, and structured Skills.

    Hyperspell stores the searchable memory layer. The local agent passes a
    stable user id so memories remain scoped to this OmniForge runtime.
    """

    def __init__(self, user_id: str | None = None) -> None:
        self._settings = settings()
        self._user_id = user_id or self._settings.hyperspell_user_id
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            if not self._settings.hyperspell_api_key:
                raise RuntimeError("HYPERSPELL_API_KEY is required for MemoryStore")

            from hyperspell import Hyperspell

            self._client = Hyperspell(
                api_key=self._settings.hyperspell_api_key,
                user_id=self._user_id,
            )

        return self._client

    def _metadata(self, kind: str, **extra: Any) -> dict[str, Any]:
        return {
            "kind": kind,
            **extra,
        }

    async def append_event(self, event: AgentEvent) -> None:
        """Persist an agent event as searchable operational memory."""
        self.client.memories.add(
            text=json.dumps(event.model_dump(mode="json"), indent=2),
            title=f"Agent event: {event.event_type}",
            resource_id=f"event:{event.id}",
            collection=self._settings.hyperspell_collection,
            metadata=self._metadata(
                "agent_event",
                event_type=str(event.event_type),
                cycle=str(event.cycle),
                snapshot_id=event.snapshot_id,
            ),
        )

    async def upsert_skill(self, skill: Skill) -> None:
        """Persist a skill as reusable procedural memory."""
        self.client.memories.add(
            text=json.dumps(skill.model_dump(mode="json"), indent=2),
            title=f"Skill: {skill.name}",
            resource_id=f"skill:{skill.name}:v{skill.version}",
            collection=self._settings.hyperspell_collection,
            metadata=self._metadata(
                "skill",
                skill_name=skill.name,
                version=str(skill.version),
                status=str(skill.status),
                source=str(skill.source),
            ),
        )

    async def append_research_note(self, note: ResearchNote) -> None:
        """Persist a structured Research Note without provider internals."""
        self.client.memories.add(
            text=json.dumps(note.model_dump(mode="json"), indent=2),
            title=f"Research Note: {note.query}",
            resource_id=f"research:{_stable_id(note.query)}",
            collection=self._settings.hyperspell_collection,
            metadata=self._metadata(
                "research_note",
                query=note.query,
                confidence=str(note.confidence),
            ),
        )

    async def upsert_game_profile(self, profile: GameProfile) -> None:
        """Persist durable Game Profile context for future Brain cycles."""
        self.client.memories.add(
            text=json.dumps(profile.model_dump(mode="json"), indent=2),
            title=f"Game Profile: {profile.game_name}",
            resource_id=f"game_profile:{_stable_id(profile.game_name)}",
            collection=self._settings.hyperspell_collection,
            metadata=self._metadata(
                "game_profile",
                game_name=profile.game_name,
                source=str(profile.source),
                confidence=str(profile.confidence),
            ),
        )

    async def context(self, query: str = "relevant OmniForge agent memories") -> str:
        """Return concise memory context for planning and recovery."""
        response = self.client.memories.search(
            query=query,
            sources=self._settings.hyperspell_sources,
            answer=True,
            max_results=8,
            options={
                "filter": {"collection": self._settings.hyperspell_collection},
            },
        )

        answer = getattr(response, "answer", None)
        if answer:
            return str(answer)

        documents = getattr(response, "documents", None) or []
        snippets: list[str] = []
        for document in documents:
            summary = getattr(document, "summary", None)
            text = getattr(document, "text", None)
            snippets.append(str(summary or text or document))

        return "\n\n".join(snippets)


def _stable_id(value: str) -> str:
    return "-".join(value.strip().lower().split())[:80] or "unknown"
