"""ElevenLabs narrator for OmniPlay-MC.

Triggered on selected Agent Events (`goal_received`, `verification_completed`,
`skill_promoted`). Synthesis runs fire-and-forget on a background thread so
the AgentLoop never blocks on TTS latency. The mp3 is written to
`outputs/narration/<id>.mp3`; the audio path/URL is mirrored to Convex via
`MemoryStore.add_narration` so the dashboard's NarrationPlayer can autoplay.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from models import AgentEventType, NarrationClip

LOG = logging.getLogger("omniplay.voice")

DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # "Rachel"
DEFAULT_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5")
DEFAULT_OUTPUT_DIR = Path(os.getenv("OMNIPLAY_NARRATION_DIR", "outputs/narration"))
BRAIN_API_URL = os.getenv("BRAIN_API_URL", "http://localhost:8000")


class Narrator:
    """Async-safe ElevenLabs TTS dispatcher with disk + Convex mirroring."""

    def __init__(
        self,
        *,
        memory: "MemoryStore | None" = None,
        api_key: str | None = None,
        voice_id: str | None = None,
        model_id: str | None = None,
        output_dir: Path | str | None = None,
        triggers: Iterable[AgentEventType] | None = None,
    ) -> None:
        self.memory = memory
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or DEFAULT_VOICE_ID
        self.model_id = model_id or DEFAULT_MODEL_ID
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.triggers: set[AgentEventType] = set(
            triggers
            or [
                AgentEventType.GOAL_RECEIVED,
                AgentEventType.VERIFICATION_COMPLETED,
                AgentEventType.SKILL_PROMOTED,
            ]
        )
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="narrator")
        self._client = self._init_client()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._memory_futures: set[asyncio.Future[None]] = set()

    def _init_client(self):
        if not self.api_key:
            LOG.info("ELEVENLABS_API_KEY not set; narrator runs in disabled mode")
            return None
        try:
            from elevenlabs.client import ElevenLabs

            return ElevenLabs(api_key=self.api_key)
        except Exception as exc:
            LOG.warning("elevenlabs client init failed: %s", exc)
            return None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Capture the asyncio loop so background threads can post mirrors back."""
        self._loop = loop

    def fire_and_forget(self, text: str, triggered_by: AgentEventType | None = None) -> str:
        """Schedule TTS without blocking. Returns the clip id (used for Convex matching)."""
        clip_id = uuid.uuid4().hex
        if not self.enabled:
            LOG.debug("narrator disabled; skipping clip for %r", text[:80])
            return clip_id
        self._executor.submit(self._render_and_publish, clip_id, text, triggered_by)
        return clip_id

    def shutdown(self) -> None:
        for fut in list(self._memory_futures):
            fut.cancel()
        self._memory_futures.clear()
        self._executor.shutdown(wait=True, cancel_futures=False)

    def _render_and_publish(
        self,
        clip_id: str,
        text: str,
        triggered_by: AgentEventType | None,
    ) -> None:
        try:
            audio_bytes = self._synthesize(text)
        except Exception as exc:
            LOG.warning("ElevenLabs synthesis failed for clip %s: %s", clip_id, exc)
            audio_bytes = b""

        path: Path | None = None
        if audio_bytes:
            path = self.output_dir / f"{clip_id}.mp3"
            try:
                path.write_bytes(audio_bytes)
            except Exception as exc:
                LOG.warning("failed to write %s: %s", path, exc)
                path = None

        audio_url = f"{BRAIN_API_URL}/narration/{clip_id}" if path else None
        clip = NarrationClip(
            id=clip_id,
            text=text,
            voice_id=self.voice_id,
            audio_url=audio_url,
            audio_path=str(path) if path else None,
            duration_ms=None,
            created_at=datetime.now(timezone.utc).isoformat(),
            triggered_by=triggered_by,
        )

        if self.memory is not None and self._loop is not None:
            try:
                fut = asyncio.run_coroutine_threadsafe(
                    self.memory.add_narration(clip), self._loop
                )
                self._memory_futures.add(fut)

                def _on_done(f: "asyncio.Future[None]") -> None:
                    self._memory_futures.discard(f)
                    exc = f.exception() if not f.cancelled() else None
                    if exc:
                        LOG.warning("narration mirror to memory failed: %s", exc)

                fut.add_done_callback(_on_done)
            except Exception as exc:
                LOG.warning("narration mirror to memory failed (schedule): %s", exc)

    def _synthesize(self, text: str) -> bytes:
        client = self._client
        if client is None:
            return b""
        chunks: Sequence[bytes] = client.text_to_speech.convert(
            voice_id=self.voice_id,
            model_id=self.model_id,
            text=text,
            output_format="mp3_44100_128",
        )
        return b"".join(chunks)


# avoid a hard-import cycle
from memory_store import MemoryStore  # noqa: E402  (used only for type hint)


__all__ = ["Narrator"]
