"""TDD: snapshot_utils.compress_snapshot() must trim large world snapshots.

RED:  run before creating brain/snapshot_utils.py — will fail with ImportError.
GREEN: pass once snapshot_utils.py is created.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))


def test_compress_snapshot_limits_nearby_blocks():
    """compress_snapshot must keep only the top max_blocks distinct block types."""
    from snapshot_utils import compress_snapshot

    big = {
        "nearby_blocks": ["stone"] * 100 + ["dirt"] * 50 + ["oak_log"] * 30,
        "nearby_entities": [],
    }
    out = compress_snapshot(big, max_blocks=5)

    assert len(out["nearby_blocks"]) <= 5, (
        f"Expected <=5 block entries, got {len(out['nearby_blocks'])}"
    )


def test_compress_snapshot_removes_raw_state():
    """compress_snapshot must strip raw_state (large, not useful for LLM prompts)."""
    from snapshot_utils import compress_snapshot

    snap = {"raw_state": {"huge": "blob"}, "nearby_blocks": []}
    out = compress_snapshot(snap)
    assert "raw_state" not in out, "raw_state must be stripped by compress_snapshot"


def test_compress_snapshot_preserves_entities():
    """Entity info (usually small) must be kept intact."""
    from snapshot_utils import compress_snapshot

    entities = [{"type": "zombie", "distance": 5.2}, {"type": "creeper", "distance": 8.1}]
    snap = {"nearby_blocks": [], "nearby_entities": entities}
    out = compress_snapshot(snap)

    assert out["nearby_entities"] == entities, (
        "compress_snapshot must preserve nearby_entities unchanged"
    )


def test_compress_snapshot_top_n_by_frequency():
    """The retained blocks must be the most frequent types."""
    from snapshot_utils import compress_snapshot

    snap = {
        "nearby_blocks": ["stone"] * 50 + ["dirt"] * 30 + ["gravel"] * 20
        + ["sand"] * 10 + ["clay"] * 5 + ["rare_ore"] * 1,
        "nearby_entities": [],
    }
    out = compress_snapshot(snap, max_blocks=3)

    # stone (50), dirt (30), gravel (20) should be top-3
    blocks = out["nearby_blocks"]
    assert "stone" in blocks, "stone (most frequent) must be in top-3"
    assert "dirt" in blocks, "dirt (2nd most frequent) must be in top-3"
    assert "gravel" in blocks, "gravel (3rd most frequent) must be in top-3"
    assert "rare_ore" not in blocks, "rare_ore (least frequent) must be excluded"


def test_compress_snapshot_small_block_list_unchanged():
    """When block count is already within max_blocks, do not modify the list."""
    from snapshot_utils import compress_snapshot

    blocks = ["stone", "dirt", "oak_log"]
    snap = {"nearby_blocks": blocks[:], "nearby_entities": []}
    out = compress_snapshot(snap, max_blocks=20)

    # All original types should still be present
    for b in blocks:
        assert b in out["nearby_blocks"], f"{b} should remain when under max_blocks"


def test_compress_snapshot_preserves_other_fields():
    """All fields other than nearby_blocks and raw_state must be passed through."""
    from snapshot_utils import compress_snapshot

    snap = {
        "position": {"x": 10, "y": 64, "z": -30},
        "health": 20,
        "inventory": {"oak_log": 4},
        "nearby_blocks": ["stone"] * 5,
        "raw_state": "junk",
    }
    out = compress_snapshot(snap)

    assert out["position"] == snap["position"]
    assert out["health"] == 20
    assert out["inventory"] == {"oak_log": 4}
