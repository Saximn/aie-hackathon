"""Slice 2 (TDD): deterministic verifier for simple Voyager goals.

Skipping the LLM critic on tasks like ``collect 4 oak_log`` saves ~6s/cycle —
the inventory delta is the ground-truth verdict.

RED:  module does not exist yet.
GREEN: ``DeterministicVerifier`` matches collect/mine/craft/kill patterns and
       returns a verdict dict, or ``None`` for ambiguous tasks.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))


def _snap(inventory=None, nearby_entities=None):
    return {
        "inventory": inventory or {},
        "nearbyBlocks": [],
        "nearbyEntities": nearby_entities or [],
        "position": {"x": 0, "y": 64, "z": 0},
    }


# ---------------------------------------------------------------------------
# can_verify
# ---------------------------------------------------------------------------

def test_can_verify_collect_task():
    from deterministic_verifier import DeterministicVerifier

    assert DeterministicVerifier().can_verify("collect 4 oak_log") is True


def test_can_verify_mine_task():
    from deterministic_verifier import DeterministicVerifier

    assert DeterministicVerifier().can_verify("mine 3 stone") is True


def test_can_verify_craft_task():
    from deterministic_verifier import DeterministicVerifier

    assert DeterministicVerifier().can_verify("craft 1 wooden_pickaxe") is True


def test_can_verify_kill_task():
    from deterministic_verifier import DeterministicVerifier

    assert DeterministicVerifier().can_verify("kill 2 zombie") is True


def test_can_verify_returns_false_for_complex_task():
    from deterministic_verifier import DeterministicVerifier

    assert DeterministicVerifier().can_verify("explore the cave") is False
    assert DeterministicVerifier().can_verify("build a shelter") is False


# ---------------------------------------------------------------------------
# verify — collect / mine
# ---------------------------------------------------------------------------

def test_collect_oak_log_success():
    """When inventory of the target item increases by >= N, verdict is success."""
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={"oak_log": 0})
    after = _snap(inventory={"oak_log": 4})

    result = DeterministicVerifier().verify("collect 4 oak_log", before, after)
    assert result is not None
    assert result["verdict"] == "success", f"expected success, got {result}"


def test_collect_oak_log_partial_is_failure():
    """Inventory delta < N → not yet complete → failure verdict."""
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={"oak_log": 0})
    after = _snap(inventory={"oak_log": 2})

    result = DeterministicVerifier().verify("collect 4 oak_log", before, after)
    assert result is not None
    assert result["verdict"] == "failure"
    assert "2" in result.get("reason", "") or "oak_log" in result.get("reason", "")


def test_collect_oak_log_no_change_is_failure():
    """Same inventory before/after → failure."""
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={"oak_log": 0})
    after = _snap(inventory={"oak_log": 0})

    result = DeterministicVerifier().verify("collect 4 oak_log", before, after)
    assert result is not None
    assert result["verdict"] == "failure"


def test_mine_uses_inventory_delta():
    """`mine N block` is verified the same way as collect (block enters inv)."""
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={"cobblestone": 1})
    after = _snap(inventory={"cobblestone": 6})

    result = DeterministicVerifier().verify("mine 3 cobblestone", before, after)
    assert result is not None
    assert result["verdict"] == "success"


def test_collect_handles_missing_before_inventory_key():
    """Item missing from `before` inventory should be treated as zero."""
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={})
    after = _snap(inventory={"dirt": 5})

    result = DeterministicVerifier().verify("collect 5 dirt", before, after)
    assert result is not None
    assert result["verdict"] == "success"


# ---------------------------------------------------------------------------
# verify — craft
# ---------------------------------------------------------------------------

def test_craft_success_when_item_present_after():
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={"oak_planks": 4})
    after = _snap(inventory={"oak_planks": 0, "wooden_pickaxe": 1})

    result = DeterministicVerifier().verify("craft 1 wooden_pickaxe", before, after)
    assert result is not None
    assert result["verdict"] == "success"


def test_craft_failure_when_item_not_added():
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={"oak_planks": 4})
    after = _snap(inventory={"oak_planks": 4})

    result = DeterministicVerifier().verify("craft 1 wooden_pickaxe", before, after)
    assert result is not None
    assert result["verdict"] == "failure"


# ---------------------------------------------------------------------------
# verify — kill
# ---------------------------------------------------------------------------

def test_kill_success_when_entity_count_drops():
    """`kill N entity` succeeds when nearby entity-type count drops by >= N."""
    from deterministic_verifier import DeterministicVerifier

    before = _snap(nearby_entities=["zombie", "zombie", "zombie", "skeleton"])
    after = _snap(nearby_entities=["skeleton"])

    result = DeterministicVerifier().verify("kill 2 zombie", before, after)
    assert result is not None
    assert result["verdict"] == "success"


def test_kill_failure_when_entity_still_present():
    from deterministic_verifier import DeterministicVerifier

    before = _snap(nearby_entities=["zombie", "zombie"])
    after = _snap(nearby_entities=["zombie", "zombie"])

    result = DeterministicVerifier().verify("kill 2 zombie", before, after)
    assert result is not None
    assert result["verdict"] == "failure"


# ---------------------------------------------------------------------------
# verify — inconclusive
# ---------------------------------------------------------------------------

def test_inconclusive_returns_none():
    """Tasks the verifier doesn't recognise must return None (caller falls back)."""
    from deterministic_verifier import DeterministicVerifier

    before = _snap()
    after = _snap()

    assert DeterministicVerifier().verify("explore the cave", before, after) is None
    assert DeterministicVerifier().verify("build a shelter", before, after) is None


def test_count_defaults_to_one_when_omitted():
    """`collect oak_log` (no number) should be treated as count=1."""
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={})
    after = _snap(inventory={"oak_log": 1})

    result = DeterministicVerifier().verify("collect oak_log", before, after)
    assert result is not None
    assert result["verdict"] == "success"


def test_case_insensitive_task_matching():
    from deterministic_verifier import DeterministicVerifier

    before = _snap(inventory={})
    after = _snap(inventory={"oak_log": 4})

    result = DeterministicVerifier().verify("Collect 4 OAK_LOG", before, after)
    assert result is not None
    assert result["verdict"] == "success"
