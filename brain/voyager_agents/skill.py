"""SkillManager — code-as-policy skill store with vector retrieval.

Each skill is stored locally in a ChromaDB collection and (optionally) mirrored
to Convex by `memory_store.py`. Embeddings are produced via the shared
`LLMClient.embed` so we don't pull in `chromadb`'s default embedding stack.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from embedding_cache import default_cache
from llm_client import LLMClient, default_client

LOG = logging.getLogger("omniplay.skill")

DEFAULT_CHROMA_DIR = Path(os.getenv("CHROMA_DIR", ".chroma"))
DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION", "omniplay_skills")


@dataclass
class SkillRecord:
    name: str
    goal: str
    code: str
    description: str
    version: int = 1
    tags: list[str] | None = None
    created_at: str = ""
    last_used_at: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "goal": self.goal,
            "description": self.description,
            "version": self.version,
            "tags": json.dumps(self.tags or []),
            "created_at": self.created_at,
            "last_used_at": self.last_used_at or "",
        }

    @classmethod
    def from_storage(cls, document: str, metadata: dict[str, Any]) -> "SkillRecord":
        return cls(
            name=str(metadata.get("name", "unnamed")),
            goal=str(metadata.get("goal", "")),
            code=document,
            description=str(metadata.get("description", "")),
            version=int(metadata.get("version", 1)),
            tags=json.loads(metadata.get("tags") or "[]"),
            created_at=str(metadata.get("created_at", "")),
            last_used_at=str(metadata.get("last_used_at") or "") or None,
        )


@dataclass
class RetrievedSkill:
    record: SkillRecord
    score: float

    def as_prompt_dict(self) -> dict[str, str]:
        return {
            "name": self.record.name,
            "goal": self.record.goal,
            "description": self.record.description,
            "code": self.record.code,
        }


class SkillManager:
    """ChromaDB-backed skill library."""

    def __init__(
        self,
        *,
        llm: LLMClient | None = None,
        persist_dir: Path | str | None = None,
        collection_name: str | None = None,
    ) -> None:
        self.llm = llm or default_client()
        self.persist_dir = Path(persist_dir) if persist_dir else DEFAULT_CHROMA_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or DEFAULT_COLLECTION
        self._client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return int(self._collection.count())

    def upsert(self, record: SkillRecord) -> SkillRecord:
        if not record.created_at:
            record.created_at = datetime.now(timezone.utc).isoformat()
        existing = self._get_by_name(record.name)
        if existing is not None:
            record.version = max(record.version, existing.version + 1)
        embedding = self._embed_skill(record)
        self._collection.upsert(
            ids=[record.name],
            documents=[record.code],
            metadatas=[record.to_metadata()],
            embeddings=[embedding],
        )
        LOG.info("upserted skill %s v%s", record.name, record.version)
        return record

    def upsert_many(self, records: list[SkillRecord]) -> None:
        if not records:
            return
        embeddings = self.llm.embed([self._skill_index_text(r) for r in records])
        for record, embedding in zip(records, embeddings, strict=True):
            if not record.created_at:
                record.created_at = datetime.now(timezone.utc).isoformat()
            self._collection.upsert(
                ids=[record.name],
                documents=[record.code],
                metadatas=[record.to_metadata()],
                embeddings=[embedding],
            )
        LOG.info("upserted %d skills", len(records))

    def retrieve(self, query: str, *, k: int = 3) -> list[RetrievedSkill]:
        if self.count() == 0:
            return []
        embedding = default_cache().get_or_compute(query, lambda t: self.llm.embed([t])[0])
        result = self._collection.query(query_embeddings=[embedding], n_results=k)
        retrieved: list[RetrievedSkill] = []
        ids = result.get("ids") or [[]]
        docs = result.get("documents") or [[]]
        metas = result.get("metadatas") or [[]]
        distances = result.get("distances") or [[]]
        for _id, doc, meta, dist in zip(ids[0], docs[0], metas[0], distances[0], strict=True):
            record = SkillRecord.from_storage(doc, meta or {})
            retrieved.append(RetrievedSkill(record=record, score=1.0 - float(dist or 0.0)))
        return retrieved

    def list_all(self) -> list[SkillRecord]:
        result = self._collection.get()
        records: list[SkillRecord] = []
        ids = result.get("ids") or []
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        for _id, doc, meta in zip(ids, docs, metas, strict=True):
            records.append(SkillRecord.from_storage(doc, meta or {}))
        return records

    def _get_by_name(self, name: str) -> SkillRecord | None:
        result = self._collection.get(ids=[name])
        ids = result.get("ids") or []
        if not ids:
            return None
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        return SkillRecord.from_storage(docs[0], metas[0] or {})

    def _embed_skill(self, record: SkillRecord) -> list[float]:
        return self.llm.embed([self._skill_index_text(record)])[0]

    @staticmethod
    def _skill_index_text(record: SkillRecord) -> str:
        return f"{record.name}\nGoal: {record.goal}\nDescription: {record.description}"


__all__ = ["RetrievedSkill", "SkillManager", "SkillRecord"]
