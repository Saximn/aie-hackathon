"""Tests for brain/task_decomposer.py."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "brain"))

from task_decomposer import TaskDecomposer


def test_atomic_task_returns_single_item():
    """Atomic tasks (matching _ATOMIC_PATTERNS) are returned as-is without calling LLM."""
    decomposer = TaskDecomposer(llm=None)
    result = decomposer.decompose("collect 4 oak_log")
    assert result == ["collect 4 oak_log"]


def test_mine_is_atomic():
    decomposer = TaskDecomposer(llm=None)
    assert decomposer.decompose("mine 16 cobblestone") == ["mine 16 cobblestone"]


def test_craft_is_atomic():
    decomposer = TaskDecomposer(llm=None)
    assert decomposer.decompose("craft 1 wooden_pickaxe") == ["craft 1 wooden_pickaxe"]


def test_complex_task_with_no_llm_returns_as_is():
    """Non-atomic task with llm=None falls back to returning the task unchanged."""
    decomposer = TaskDecomposer(llm=None)
    complex_task = "build a small dirt shelter and survive the night"
    result = decomposer.decompose(complex_task)
    assert result == [complex_task]


def test_complex_task_calls_llm_and_parses_numbered_list():
    """Non-atomic task with a mock LLM returns parsed sub-tasks."""
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "1. do A\n2. do B"

    decomposer = TaskDecomposer(llm=mock_llm)
    result = decomposer.decompose("build a base and gather resources")

    mock_llm.complete.assert_called_once()
    assert result == ["do A", "do B"]


def test_llm_result_capped_at_five():
    """LLM output with more than 5 items is capped at 5."""
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "\n".join(f"{i}. step {i}" for i in range(1, 8))

    decomposer = TaskDecomposer(llm=mock_llm)
    result = decomposer.decompose("do a complex multi-step operation")

    assert len(result) == 5


def test_llm_failure_falls_back_to_original_task():
    """If the LLM raises, the original task is returned unchanged."""
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = RuntimeError("network error")

    decomposer = TaskDecomposer(llm=mock_llm)
    task = "explore the world and find diamonds"
    result = decomposer.decompose(task)

    assert result == [task]


def test_is_atomic_go_to():
    decomposer = TaskDecomposer()
    assert decomposer.is_atomic("go to the nearest village")
    assert decomposer.is_atomic("walk to the river")
    assert decomposer.is_atomic("move to coordinates")


def test_is_atomic_equip():
    decomposer = TaskDecomposer()
    assert decomposer.is_atomic("equip iron sword")


def test_is_atomic_eat():
    decomposer = TaskDecomposer()
    assert decomposer.is_atomic("eat bread")


def test_empty_llm_response_returns_original_task():
    """Empty LLM response does not produce an empty list."""
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "   \n  "

    decomposer = TaskDecomposer(llm=mock_llm)
    task = "build a house with a roof"
    result = decomposer.decompose(task)

    assert result == [task]
