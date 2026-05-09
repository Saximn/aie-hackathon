"""LRU cache for skill-retrieval task embeddings.

The Voyager curriculum often re-asks the same task ("collect 4 oak_log") on
every cycle.  Each retrieval calls ``LLMClient.embed`` which hits OpenAI for
~0.5s.  Caching the embedding by a normalised key removes the round-trip on
hits.

Pure stdlib (``collections.OrderedDict``) — no extra pip deps.

Friend's one-line wiring inside ``voyager_agents/skill.py``::

    from embedding_cache import default_cache
    embedding = default_cache().get_or_compute(query, lambda t: self.llm.embed([t])[0])

The cache is process-wide via :func:`default_cache`; tests can build their own
``EmbeddingCache(max_size=...)`` for isolation.
"""

from __future__ import annotations

import re
import threading
from collections import OrderedDict
from typing import Callable

DEFAULT_MAX_SIZE = 512

# Collapse runs of whitespace so superficial formatting differences hit the
# same cache slot.  We do NOT strip punctuation — the embedder weights it.
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Lowercase + collapse whitespace for cache-key equality."""
    return _WHITESPACE_RE.sub(" ", text.strip().lower())


class EmbeddingCache:
    """Thread-safe LRU cache mapping normalised text → embedding vector."""

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE) -> None:
        if max_size <= 0:
            raise ValueError(f"max_size must be > 0, got {max_size}")
        self._max_size = max_size
        self._store: "OrderedDict[str, list[float]]" = OrderedDict()
        self._lock = threading.Lock()

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)

    def get_or_compute(
        self,
        text: str,
        compute_fn: Callable[[str], list[float]],
    ) -> list[float]:
        """Return cached embedding for *text*, computing & caching it on miss.

        - The normalised text becomes the cache key.
        - On hit, the entry is moved to the most-recently-used end.
        - On miss, ``compute_fn`` is called with the *original* text (so the
          embedder sees what the caller passed) and the result is cached.
        """
        key = _normalize(text)
        with self._lock:
            cached = self._store.get(key)
            if cached is not None:
                self._store.move_to_end(key)
                return cached

        # Compute outside the lock — embedders make network calls.
        embedding = compute_fn(text)

        with self._lock:
            self._store[key] = embedding
            self._store.move_to_end(key)
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)
        return embedding

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


_DEFAULT: EmbeddingCache | None = None
_DEFAULT_LOCK = threading.Lock()


def default_cache() -> EmbeddingCache:
    """Process-wide singleton, lazily constructed."""
    global _DEFAULT
    if _DEFAULT is None:
        with _DEFAULT_LOCK:
            if _DEFAULT is None:
                _DEFAULT = EmbeddingCache()
    return _DEFAULT


__all__ = ["EmbeddingCache", "default_cache"]
