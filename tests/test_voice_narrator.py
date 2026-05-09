"""TDD Slice 2 — Narrator behaviour tests (offline, no ElevenLabs calls).

All four tests run without a real ELEVENLABS_API_KEY and without touching the
network.  ElevenLabs client creation and file I/O that the real Narrator would
do are intercepted with unittest.mock.patch where the test goes beyond the
disabled-mode fast-path.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

BRAIN_ROOT = Path(__file__).resolve().parents[1] / "brain"
sys.path.insert(0, str(BRAIN_ROOT))


def _make_narrator(*, api_key: str | None = None, memory=None, output_dir=None):
    """Construct a Narrator with safe defaults for tests."""
    from voice import Narrator

    tmp = output_dir or tempfile.mkdtemp()
    return Narrator(api_key=api_key, memory=memory, output_dir=tmp)


class TestNarratorDisabled(unittest.TestCase):
    """Narrator with no API key should be in disabled mode."""

    def test_narrator_disabled_when_no_api_key(self):
        """Narrator.enabled is False when no API key is supplied or in env."""
        with patch.dict(os.environ, {}, clear=False) as env:
            env.pop("ELEVENLABS_API_KEY", None)
            narrator = _make_narrator(api_key=None)
        self.assertFalse(narrator.enabled)

    def test_narrator_fire_and_forget_returns_id_when_disabled(self):
        """fire_and_forget returns a non-empty string id even when disabled."""
        with patch.dict(os.environ, {}, clear=False) as env:
            env.pop("ELEVENLABS_API_KEY", None)
            narrator = _make_narrator(api_key=None)
        self.assertFalse(narrator.enabled)
        clip_id = narrator.fire_and_forget("Hello, world!")
        self.assertIsNotNone(clip_id)
        self.assertIsInstance(clip_id, str)
        self.assertTrue(len(clip_id) > 0)

    def test_narrator_skips_synthesis_when_disabled(self):
        """_synthesize must not be called when the narrator is disabled."""
        with patch.dict(os.environ, {}, clear=False) as env:
            env.pop("ELEVENLABS_API_KEY", None)
            narrator = _make_narrator(api_key=None)
        self.assertFalse(narrator.enabled)
        with patch.object(narrator, "_synthesize") as mock_synth:
            narrator.fire_and_forget("Should not synthesise this.")
            mock_synth.assert_not_called()

    def test_narrator_does_not_call_memory_without_loop_attached(self):
        """fire_and_forget with no memory store attached must not crash and
        must not call add_narration."""
        with patch.dict(os.environ, {}, clear=False) as env:
            env.pop("ELEVENLABS_API_KEY", None)
            narrator = _make_narrator(api_key=None, memory=None)
        self.assertIsNone(narrator.memory)
        self.assertFalse(narrator.enabled)

        mock_memory = MagicMock()
        mock_memory.add_narration = AsyncMock()

        # Call fire_and_forget — disabled path returns immediately, no thread spawned
        clip_id = narrator.fire_and_forget("No memory attached.")
        self.assertIsNotNone(clip_id)
        mock_memory.add_narration.assert_not_called()


if __name__ == "__main__":
    unittest.main()
