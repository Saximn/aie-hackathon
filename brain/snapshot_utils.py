"""Utilities for compressing WorldSnapshot dicts before serialising into LLM prompts.

Large ``nearby_blocks`` arrays (hundreds of entries) inflate the token count
and slow down tokenisation.  ``compress_snapshot`` keeps only the top-N most
frequent block types and strips heavy fields that are not useful for planning.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

_STRIPPED_KEYS = frozenset({"raw_state"})


def compress_snapshot(snapshot: dict[str, Any], max_blocks: int = 20) -> dict[str, Any]:
    """Return a slimmer copy of *snapshot* safe to serialise into an LLM prompt.

    Changes made:
    - ``raw_state`` (large opaque blob) is removed.
    - ``nearby_blocks`` is deduplicated and capped at the *max_blocks* most
      frequent distinct block types.  All other fields are passed through as-is.

    Args:
        snapshot:   The raw WorldSnapshot dict from the observer.
        max_blocks: Maximum number of distinct block types to retain.

    Returns:
        A new dict — the original is never mutated.
    """
    out: dict[str, Any] = {k: v for k, v in snapshot.items() if k not in _STRIPPED_KEYS}

    blocks: list[str] = out.get("nearby_blocks", [])
    if len(blocks) > max_blocks:
        counts = Counter(blocks)
        top_types = [block_type for block_type, _ in counts.most_common(max_blocks)]
        out["nearby_blocks"] = top_types

    return out


__all__ = ["compress_snapshot"]
