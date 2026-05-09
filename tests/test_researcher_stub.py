"""TDD Slice 2 — Researcher stub behaviour tests.

Researcher is explicitly a stub module (out of scope for the hackathon build).
These tests verify the documented disabled-by-default contract without hitting
any external network.
"""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

BRAIN_ROOT = Path(__file__).resolve().parents[1] / "brain"
sys.path.insert(0, str(BRAIN_ROOT))


class TestResearcherStub(unittest.TestCase):

    def _make_researcher(self):
        from researcher import Researcher
        return Researcher()

    def test_researcher_disabled_by_default(self):
        """Researcher.enabled is False with no backend configured."""
        researcher = self._make_researcher()
        self.assertFalse(researcher.enabled)

    def test_lookup_returns_none_when_disabled(self):
        """lookup() returns None for any query when disabled."""
        researcher = self._make_researcher()
        result = asyncio.run(researcher.lookup("how do I craft a pickaxe?"))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
