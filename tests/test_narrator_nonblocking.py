"""Narrator memory write must be non-blocking.

Behavioural test: when memory.add_narration is slow, fire_and_forget
(and the background render thread) must NOT block for longer than the
synthesis itself. The memory write is fire-and-forget — a slow write
must not stall the narrator thread.
"""
import asyncio
import sys
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))

from voice import Narrator
from models import AgentEventType


class SlowMemory:
    """Fake MemoryStore whose add_narration sleeps for 5 seconds."""

    def __init__(self):
        self.called = threading.Event()

    async def add_narration(self, clip):
        self.called.set()
        await asyncio.sleep(5)


def test_render_and_publish_does_not_block_on_slow_memory(tmp_path):
    """_render_and_publish must return quickly even if memory.add_narration is slow."""
    memory = SlowMemory()
    narrator = Narrator(
        api_key=None,  # disabled — no real synthesis
        memory=memory,
        output_dir=tmp_path,
    )
    loop = asyncio.new_event_loop()
    narrator.attach_loop(loop)

    # Run the loop in a background thread so it can process coroutines
    loop_thread = threading.Thread(target=loop.run_forever, daemon=True)
    loop_thread.start()

    try:
        start = time.monotonic()
        # Call the internal method directly — it runs on a thread
        narrator._render_and_publish("clip001", "hello world", AgentEventType.GOAL_RECEIVED)
        elapsed = time.monotonic() - start

        # Must complete in well under 2 seconds (synthesis is skipped; only memory write)
        assert elapsed < 2.0, f"_render_and_publish blocked for {elapsed:.1f}s on slow memory"
    finally:
        loop.call_soon_threadsafe(loop.stop)
        loop_thread.join(timeout=1)
        narrator.shutdown()
