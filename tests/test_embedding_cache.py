"""Slice 3 (TDD): LRU cache for skill-retrieval embeddings.

Repeated curriculum tasks ("collect 4 oak_log") embed the same string each
cycle.  Caching the embedding shaves the ~0.5s OpenAI embeddings round-trip on
hits, with a normalised key so superficial whitespace/case differences hit too.

RED:   module does not exist yet.
GREEN: ``EmbeddingCache.get_or_compute`` returns cached values, normalises
       keys, and evicts least-recently-used entries when ``max_size`` is hit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))


# ---------------------------------------------------------------------------
# Hit / miss
# ---------------------------------------------------------------------------

def test_cache_hit_returns_same_embedding_without_recompute():
    from embedding_cache import EmbeddingCache

    cache = EmbeddingCache(max_size=8)
    calls = 0

    def compute(text: str) -> list[float]:
        nonlocal calls
        calls += 1
        return [float(len(text)), 0.0, 0.0]

    first = cache.get_or_compute("collect 4 oak_log", compute)
    second = cache.get_or_compute("collect 4 oak_log", compute)

    assert first == second
    assert calls == 1, f"compute should run once on cache hit, got {calls} calls"


def test_cache_miss_invokes_compute_once_per_unique_text():
    from embedding_cache import EmbeddingCache

    cache = EmbeddingCache(max_size=8)
    calls = []

    def compute(text: str) -> list[float]:
        calls.append(text)
        return [float(len(text))]

    cache.get_or_compute("task A", compute)
    cache.get_or_compute("task B", compute)
    cache.get_or_compute("task A", compute)
    cache.get_or_compute("task B", compute)

    assert len(calls) == 2, f"expected 2 unique computes, got {calls}"


# ---------------------------------------------------------------------------
# Normalisation (case + whitespace)
# ---------------------------------------------------------------------------

def test_normalizes_whitespace_and_case():
    from embedding_cache import EmbeddingCache

    cache = EmbeddingCache(max_size=8)
    calls = 0

    def compute(text: str) -> list[float]:
        nonlocal calls
        calls += 1
        return [1.0]

    cache.get_or_compute("collect 4 oak_log", compute)
    cache.get_or_compute("  COLLECT 4 OAK_LOG  ", compute)
    cache.get_or_compute("collect   4   oak_log", compute)

    assert calls == 1, (
        f"normalised whitespace/case should hit once, got {calls} computes"
    )


# ---------------------------------------------------------------------------
# LRU eviction
# ---------------------------------------------------------------------------

def test_lru_eviction_at_max_size():
    from embedding_cache import EmbeddingCache

    cache = EmbeddingCache(max_size=2)
    calls = []

    def compute(text: str) -> list[float]:
        calls.append(text)
        return [float(len(text))]

    cache.get_or_compute("a", compute)
    cache.get_or_compute("b", compute)
    cache.get_or_compute("c", compute)  # evicts "a"
    cache.get_or_compute("a", compute)  # cache miss again

    # "a" recomputed twice (initial + after eviction); b and c once each.
    assert calls.count("a") == 2
    assert calls.count("b") == 1
    assert calls.count("c") == 1


def test_lru_recency_promotes_on_access():
    """Accessing 'a' again before adding 'c' should evict 'b' instead of 'a'."""
    from embedding_cache import EmbeddingCache

    cache = EmbeddingCache(max_size=2)
    calls = []

    def compute(text: str) -> list[float]:
        calls.append(text)
        return [1.0]

    cache.get_or_compute("a", compute)
    cache.get_or_compute("b", compute)
    cache.get_or_compute("a", compute)  # promote a
    cache.get_or_compute("c", compute)  # evict b (LRU)
    cache.get_or_compute("a", compute)  # still cached
    cache.get_or_compute("b", compute)  # cache miss

    assert calls.count("a") == 1, "a must remain cached"
    assert calls.count("b") == 2, "b should have been evicted then recomputed"


# ---------------------------------------------------------------------------
# Stats / introspection
# ---------------------------------------------------------------------------

def test_default_cache_singleton_returns_same_instance():
    from embedding_cache import default_cache

    assert default_cache() is default_cache()


def test_size_reports_current_entries():
    from embedding_cache import EmbeddingCache

    cache = EmbeddingCache(max_size=10)
    assert cache.size == 0

    cache.get_or_compute("a", lambda _t: [0.0])
    cache.get_or_compute("b", lambda _t: [0.0])
    assert cache.size == 2

    cache.get_or_compute("a", lambda _t: [0.0])  # hit, no growth
    assert cache.size == 2
