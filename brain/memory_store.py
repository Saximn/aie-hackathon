"""Convex-backed memory store with a JSON-file fallback.

If `CONVEX_URL` is set, all writes go to the Convex deployment via the
official `convex` Python client. Otherwise we append to a local JSONL file
in `.omniplay-memory/` so dev still runs offline.

Skill data is mirrored from `voyager_agents.skill.SkillManager` (Chroma is the
local source of truth for retrieval); on agent boot we pull skills back from
Convex into Chroma for cross-session persistence.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from convex import ConvexClient

from models import AgentEvent, NarrationClip, WorldSnapshot
from voyager_agents.skill import SkillManager, SkillRecord

LOG = logging.getLogger("omniplay.memory")

LOCAL_DIR = Path(os.getenv("OMNIPLAY_LOCAL_MEMORY", ".omniplay-memory"))


class MemoryStore:
    def __init__(
        self,
        *,
        skill_manager: SkillManager,
        convex_url: str | None = None,
        episode_id: str | None = None,
    ) -> None:
        self.skill_manager = skill_manager
        self.convex_url = convex_url or os.getenv("CONVEX_URL")
        self.episode_id = episode_id or datetime.now(timezone.utc).strftime("ep-%Y%m%dT%H%M%S")
        self._client: ConvexClient | None = None
        if self.convex_url:
            try:
                self._client = ConvexClient(self.convex_url)
                LOG.info("convex memory store: %s (episode %s)", self.convex_url, self.episode_id)
            except Exception as exc:
                LOG.warning("ConvexClient init failed (%s); falling back to local JSON", exc)
                self._client = None
        if self._client is None:
            LOCAL_DIR.mkdir(parents=True, exist_ok=True)
            LOG.info("local memory store at %s (episode %s)", LOCAL_DIR.resolve(), self.episode_id)

    @property
    def using_convex(self) -> bool:
        return self._client is not None

    async def start_episode(self, *, task: str) -> None:
        meta = {
            "episodeId": self.episode_id,
            "task": task,
            "startedAt": datetime.now(timezone.utc).isoformat(),
        }
        if self._client is not None:
            await asyncio.to_thread(self._safe_mutation, "episodes:start", meta)
        else:
            self._append_local("episodes.jsonl", meta)

    async def append_event(self, event: AgentEvent) -> None:
        payload = {
            "episodeId": self.episode_id,
            "id": event.id,
            "timestamp": event.timestamp,
            "eventType": event.event_type.value,
            "cycle": event.cycle,
            "snapshotId": event.snapshot_id,
            "data": _json_safe(event.data),
        }
        if self._client is not None:
            await asyncio.to_thread(self._safe_mutation, "events:append", payload)
        else:
            self._append_local("events.jsonl", payload)

    async def set_current_state(self, snapshot: WorldSnapshot) -> None:
        payload = {
            "episodeId": self.episode_id,
            "snapshotId": snapshot.snapshot_id,
            "cycle": snapshot.cycle,
            "goal": snapshot.goal,
            "game": snapshot.game,
            "symbolic": _json_safe(snapshot.symbolic.model_dump()),
            "derived": _json_safe(snapshot.derived_risks.model_dump()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if self._client is not None:
            await asyncio.to_thread(self._safe_mutation, "state:set", payload)
        else:
            self._write_local("current_state.json", payload)

    async def upsert_skill(self, record: SkillRecord) -> None:
        payload = {
            "episodeId": self.episode_id,
            "name": record.name,
            "goal": record.goal,
            "description": record.description,
            "version": record.version,
            "tags": record.tags or [],
            "code": record.code,
            "createdAt": record.created_at,
            "lastUsedAt": record.last_used_at,
        }
        if self._client is not None:
            await asyncio.to_thread(self._safe_mutation, "skills:upsert", payload)
        else:
            self._append_local("skills.jsonl", payload)

    async def add_narration(self, clip: NarrationClip) -> None:
        payload = {
            "episodeId": self.episode_id,
            "id": clip.id,
            "text": clip.text,
            "voiceId": clip.voice_id,
            "audioUrl": clip.audio_url,
            "audioPath": clip.audio_path,
            "durationMs": clip.duration_ms,
            "createdAt": clip.created_at,
            "triggeredBy": clip.triggered_by.value if clip.triggered_by else None,
        }
        if self._client is not None:
            await asyncio.to_thread(self._safe_mutation, "narration:add", payload)
        else:
            self._append_local("narration.jsonl", payload)

    async def list_skills(self) -> list[SkillRecord]:
        """Cloud → local mirror. Used at boot to hydrate Chroma."""
        if self._client is not None:
            try:
                rows = await asyncio.to_thread(self._safe_query, "skills:list", {"episodeId": None})
            except Exception as exc:
                LOG.warning("skills:list failed (%s); falling back to local", exc)
                rows = self._read_local_jsonl("skills.jsonl")
        else:
            rows = self._read_local_jsonl("skills.jsonl")

        records: list[SkillRecord] = []
        for row in rows or []:
            try:
                records.append(
                    SkillRecord(
                        name=row.get("name", "unnamed"),
                        goal=row.get("goal", ""),
                        code=row.get("code", ""),
                        description=row.get("description", ""),
                        version=int(row.get("version") or 1),
                        tags=list(row.get("tags") or []),
                        created_at=row.get("createdAt") or row.get("created_at") or "",
                        last_used_at=row.get("lastUsedAt") or row.get("last_used_at"),
                    )
                )
            except Exception as exc:
                LOG.warning("malformed skill row dropped: %s (%s)", row, exc)
        return records

    async def hydrate_skills_into_chroma(self) -> int:
        """Pull skills from Convex/local into the Chroma SkillManager. Returns count loaded."""
        records = await self.list_skills()
        if not records:
            return 0
        existing_names = {r.name for r in self.skill_manager.list_all()}
        new_records = [r for r in records if r.name not in existing_names]
        if new_records:
            await asyncio.to_thread(self.skill_manager.upsert_many, new_records)
        return len(new_records)

    async def context(self) -> str:
        skill_count = await asyncio.to_thread(self.skill_manager.count)
        return f"episode={self.episode_id} skills={skill_count}"

    def _safe_mutation(self, name: str, payload: dict[str, Any]) -> Any:
        if self._client is None:
            raise RuntimeError("convex client not configured")
        try:
            return self._client.mutation(name, payload)
        except Exception as exc:
            LOG.warning("convex mutation %s failed (%s); writing local fallback", name, exc)
            self._append_local(f"convex_failed_{name.replace(':', '_')}.jsonl", payload)
            return None

    def _safe_query(self, name: str, payload: dict[str, Any]) -> Any:
        if self._client is None:
            raise RuntimeError("convex client not configured")
        return self._client.query(name, payload)

    def _append_local(self, filename: str, payload: dict[str, Any]) -> None:
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        path = LOCAL_DIR / filename
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(_json_safe(payload), ensure_ascii=False) + "\n")

    def _write_local(self, filename: str, payload: dict[str, Any]) -> None:
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        path = LOCAL_DIR / filename
        path.write_text(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_local_jsonl(self, filename: str) -> list[dict[str, Any]]:
        path = LOCAL_DIR / filename
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    if hasattr(value, "value"):
        return value.value
    return str(value)


__all__ = ["MemoryStore"]
