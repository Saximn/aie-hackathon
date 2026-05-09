"""DeterministicVerifier — ground-truth verdict for simple Voyager goals.

The LLM critic in :mod:`voyager_agents.critic` adds ~6s/cycle.  For tasks that
reduce to "did the inventory change by N?" the verdict is unambiguous from the
two snapshots, so we can short-circuit the critic entirely.

Supported task patterns (case-insensitive):

- ``collect [N] <item>``  → inventory delta of *item* >= N
- ``mine [N] <block>``    → inventory delta of *block* >= N
- ``craft [N] <item>``    → inventory delta of *item* >= N
- ``kill [N] <entity>``   → ``nearbyEntities`` count of *entity* drops by >= N

The verifier returns ``{"verdict": "success" | "failure", "reason": str}``
when it recognises the task.  Any unrecognised task returns ``None`` so the
caller can fall back to the LLM critic.

Intentionally a pure helper module — wire it into the loop with one line in
``agent_loop.py``::

    det = DeterministicVerifier().verify(task, snap_before_dict, snap_after_dict)
    if det is not None:
        # use det["verdict"] directly, skip CriticAgent
        ...
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Patterns are anchored with ``\b`` so they don't grab inside larger words.
_COLLECT_RE = re.compile(r"\b(?:collect|gather)\s+(?:(\d+)\s+)?(\w+)", re.IGNORECASE)
_MINE_RE = re.compile(r"\b(?:mine|dig)\s+(?:(\d+)\s+)?(\w+)", re.IGNORECASE)
_CRAFT_RE = re.compile(r"\bcraft\s+(?:(\d+)\s+)?(\w+)", re.IGNORECASE)
_KILL_RE = re.compile(r"\b(?:kill|slay)\s+(?:(\d+)\s+)?(\w+)", re.IGNORECASE)

# Order matters: collect is the most common goal in the Voyager curriculum.
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (_COLLECT_RE, "inventory_delta"),
    (_MINE_RE, "inventory_delta"),
    (_CRAFT_RE, "inventory_delta"),
    (_KILL_RE, "entity_drop"),
]


class DeterministicVerifier:
    """Stateless verifier for simple Mineflayer goals."""

    def can_verify(self, task: str) -> bool:
        """Return True iff the task matches one of the supported patterns."""
        if not task:
            return False
        return self._classify(task) is not None

    def verify(
        self,
        task: str,
        snapshot_before: dict[str, Any],
        snapshot_after: dict[str, Any],
    ) -> Optional[dict[str, str]]:
        """Return ``{"verdict": ..., "reason": ...}`` or ``None`` if ambiguous.

        The snapshot dicts are the same shape used by ``CriticAgent.judge`` —
        ``{"inventory": {item: count}, "nearbyEntities": [...], ...}``.
        """
        classification = self._classify(task)
        if classification is None:
            return None

        kind, count, target = classification
        if kind == "inventory_delta":
            return self._verify_inventory_delta(target, count, snapshot_before, snapshot_after)
        if kind == "entity_drop":
            return self._verify_entity_drop(target, count, snapshot_before, snapshot_after)
        return None

    # ------------------------------------------------------------------
    # Pattern classification
    # ------------------------------------------------------------------

    def _classify(self, task: str) -> Optional[tuple[str, int, str]]:
        """Return ``(kind, count, target)`` for the first matching pattern."""
        for pattern, kind in _PATTERNS:
            m = pattern.search(task)
            if m:
                count = int(m.group(1)) if m.group(1) else 1
                target = m.group(2).lower()
                return kind, count, target
        return None

    # ------------------------------------------------------------------
    # Verifiers
    # ------------------------------------------------------------------

    @staticmethod
    def _verify_inventory_delta(
        item: str,
        required_delta: int,
        snapshot_before: dict[str, Any],
        snapshot_after: dict[str, Any],
    ) -> dict[str, str]:
        before_count = _inv_count(snapshot_before, item)
        after_count = _inv_count(snapshot_after, item)
        delta = after_count - before_count
        if delta >= required_delta:
            return {
                "verdict": "success",
                "reason": (
                    f"inventory[{item}] gained {delta} (>= required {required_delta})"
                ),
            }
        return {
            "verdict": "failure",
            "reason": (
                f"inventory[{item}] gained {delta} of required {required_delta} "
                f"(before={before_count}, after={after_count})"
            ),
        }

    @staticmethod
    def _verify_entity_drop(
        entity: str,
        required_kills: int,
        snapshot_before: dict[str, Any],
        snapshot_after: dict[str, Any],
    ) -> dict[str, str]:
        before_count = _entity_count(snapshot_before, entity)
        after_count = _entity_count(snapshot_after, entity)
        drop = before_count - after_count
        if drop >= required_kills:
            return {
                "verdict": "success",
                "reason": (
                    f"nearby {entity} count dropped {drop} "
                    f"(>= required {required_kills})"
                ),
            }
        return {
            "verdict": "failure",
            "reason": (
                f"nearby {entity} count dropped {drop} of required {required_kills} "
                f"(before={before_count}, after={after_count})"
            ),
        }


def _inv_count(snapshot: dict[str, Any], item: str) -> int:
    inv = snapshot.get("inventory") or snapshot.get("Inventory") or {}
    if not isinstance(inv, dict):
        return 0
    target_lower = item.lower()
    for key, value in inv.items():
        if str(key).lower() == target_lower:
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0
    return 0


def _entity_count(snapshot: dict[str, Any], entity_type: str) -> int:
    entities = (
        snapshot.get("nearbyEntities")
        or snapshot.get("nearby_entities")
        or []
    )
    target_lower = entity_type.lower()
    return sum(1 for e in entities if str(e).lower() == target_lower)


__all__ = ["DeterministicVerifier"]
