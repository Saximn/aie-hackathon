"""TDD: POST /prompt endpoint must accept tasks and queue them.

RED: run before adding the /prompt route to main.py.
GREEN: pass once main.py exposes /prompt and task_queue.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))


def _get_app_and_queue():
    """Import the app fresh so module-level queue is accessible."""
    import importlib
    import main as m

    importlib.reload(m)  # reset state between tests
    return m.app, m.task_queue


def test_prompt_endpoint_returns_200_with_task_id():
    app, queue = _get_app_and_queue()
    client = TestClient(app)

    response = client.post("/prompt", json={"task": "build a dirt house"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("accepted") is True
    assert "task" in body or "queued" in body or "task_id" in body


def test_prompt_endpoint_adds_task_to_queue():
    app, queue = _get_app_and_queue()
    client = TestClient(app)

    queue.clear()
    client.post("/prompt", json={"task": "mine 10 stone"})

    assert len(queue) == 1
    assert queue[0] == "mine 10 stone"


def test_prompt_endpoint_multiple_tasks_ordered():
    app, queue = _get_app_and_queue()
    client = TestClient(app)

    queue.clear()
    client.post("/prompt", json={"task": "task A"})
    client.post("/prompt", json={"task": "task B"})
    client.post("/prompt", json={"task": "task C"})

    assert queue == ["task A", "task B", "task C"]


def test_prompt_endpoint_rejects_empty_task():
    app, queue = _get_app_and_queue()
    client = TestClient(app)

    response = client.post("/prompt", json={"task": ""})
    assert response.status_code == 422 or response.json().get("accepted") is False


def test_metrics_endpoint_exists():
    """GET /metrics must return JSON with uptime_seconds and other keys."""
    app, _ = _get_app_and_queue()
    client = TestClient(app)

    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "uptime_seconds" in body
    assert "total_cycles" in body


def test_status_endpoint_reflects_event_bus():
    """GET /status must include currentGoal and currentStatus keys."""
    app, _ = _get_app_and_queue()
    client = TestClient(app)

    response = client.get("/status")
    assert response.status_code == 200
    body = response.json()
    assert "currentGoal" in body
    assert "currentStatus" in body
