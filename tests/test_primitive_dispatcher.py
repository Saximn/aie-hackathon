"""TDD: PrimitiveDispatcher must short-circuit simple tasks without LLM calls.

RED:  run before creating brain/primitive_dispatcher.py — will fail with ImportError.
GREEN: pass once primitive_dispatcher.py is created.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))


# ---------------------------------------------------------------------------
# collect
# ---------------------------------------------------------------------------

def test_collect_task_returns_js_without_llm():
    """'collect N item' must match and return JS referencing the item."""
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    js = d.match("collect 4 oak_log")
    assert js is not None, "PrimitiveDispatcher must match 'collect 4 oak_log'"
    assert "oak_log" in js or "collectBlock" in js, (
        f"Generated JS must reference oak_log or collectBlock, got:\n{js}"
    )


def test_collect_task_case_insensitive():
    """Collect pattern must be case-insensitive."""
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    assert d.match("Collect 10 stone") is not None
    assert d.match("COLLECT 1 dirt") is not None


def test_collect_js_embeds_count():
    """Generated JS for collect must include the requested count."""
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    js = d.match("collect 7 birch_log")
    assert js is not None
    assert "7" in js, f"JS must embed count '7', got:\n{js}"


# ---------------------------------------------------------------------------
# dig / mine
# ---------------------------------------------------------------------------

def test_dig_task_returns_js():
    """'dig N item' must match and return JS."""
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    js = d.match("dig 3 stone")
    assert js is not None, "PrimitiveDispatcher must match 'dig 3 stone'"
    assert "stone" in js


def test_mine_task_returns_js():
    """'mine N item' must also match the dig/mine pattern."""
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    js = d.match("mine 5 cobblestone")
    assert js is not None, "PrimitiveDispatcher must match 'mine 5 cobblestone'"
    assert "cobblestone" in js


# ---------------------------------------------------------------------------
# go to / walk to / move to
# ---------------------------------------------------------------------------

def test_goto_task_returns_js():
    """'go to X' must match and return pathfinder JS."""
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    js = d.match("go to the village")
    assert js is not None, "PrimitiveDispatcher must match 'go to'"


def test_walk_to_returns_js():
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    assert d.match("walk to nearest tree") is not None


def test_move_to_returns_js():
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    assert d.match("move to spawn") is not None


# ---------------------------------------------------------------------------
# craft
# ---------------------------------------------------------------------------

def test_craft_task_returns_js():
    """'craft item' must match and return JS using bot.craft."""
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    js = d.match("craft wooden_pickaxe")
    assert js is not None, "PrimitiveDispatcher must match 'craft wooden_pickaxe'"
    assert "wooden_pickaxe" in js


# ---------------------------------------------------------------------------
# unknown tasks → None
# ---------------------------------------------------------------------------

def test_unknown_task_returns_none():
    """Complex tasks with no pattern match must return None."""
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    assert d.match("build a castle with dragon statues") is None


def test_ambiguous_task_returns_none():
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    assert d.match("survive the night") is None
    assert d.match("find a village and trade with villagers") is None
    assert d.match("explore the nether") is None


def test_empty_task_returns_none():
    from primitive_dispatcher import PrimitiveDispatcher

    d = PrimitiveDispatcher()
    assert d.match("") is None
