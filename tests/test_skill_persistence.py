"""Cross-session skill persistence smoke test (offline, no OpenAI/Convex).

Covers:
- SkillManager upserts a skill into Chroma (with a stub embedder).
- MemoryStore mirrors the upsert into the local JSONL fallback.
- A fresh MemoryStore + SkillManager hydrates the JSONL skills back into Chroma.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

BRAIN_ROOT = Path(__file__).resolve().parents[1] / "brain"
sys.path.insert(0, str(BRAIN_ROOT))


class StubLLM:
    """Deterministic stand-in for `LLMClient` so the test never hits OpenAI."""

    def embed(self, texts):
        return [[float((i + 1) * 0.1) for i in range(8)] for _ in texts]


def _make_record(name: str, code: str = "return 'hello';"):
    from voyager_agents.skill import SkillRecord

    return SkillRecord(
        name=name,
        goal=f"goal for {name}",
        code=code,
        description=f"desc for {name}",
        version=1,
        tags=[],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


class SkillPersistenceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Windows: chromadb keeps file handles open via mmap, so use ignore_cleanup_errors
        # and a unique-per-test root.
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._tmp.cleanup)
        chroma_dir = Path(self._tmp.name) / "chroma"
        memory_dir = Path(self._tmp.name) / "memory"
        os.environ["OMNIPLAY_LOCAL_MEMORY"] = str(memory_dir)
        os.environ["CHROMA_DIR"] = str(chroma_dir)
        os.environ.pop("CONVEX_URL", None)

    async def test_skill_persists_across_sessions(self):
        from memory_store import MemoryStore
        from voyager_agents.skill import SkillManager

        with patch("voyager_agents.skill.default_client", return_value=StubLLM()):
            sm1 = SkillManager(persist_dir=os.environ["CHROMA_DIR"], collection_name="test_skills_a")
            mem1 = MemoryStore(skill_manager=sm1, episode_id="ep-test-1")
            await mem1.start_episode(task="bootstrap")
            record = _make_record("test_chop_wood", "return await bot.chat('hi');")
            stored = sm1.upsert(record)
            await mem1.upsert_skill(stored)
            self.assertEqual(sm1.count(), 1)

            sm2 = SkillManager(persist_dir=os.environ["CHROMA_DIR"] + "_b", collection_name="test_skills_b")
            mem2 = MemoryStore(skill_manager=sm2, episode_id="ep-test-2")
            self.assertEqual(sm2.count(), 0)
            hydrated = await mem2.hydrate_skills_into_chroma()
            self.assertEqual(hydrated, 1)
            self.assertEqual(sm2.count(), 1)
            retrieved = sm2.list_all()
            self.assertEqual(retrieved[0].name, "test_chop_wood")
            self.assertIn("hi", retrieved[0].code)


if __name__ == "__main__":
    unittest.main()
