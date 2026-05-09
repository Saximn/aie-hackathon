"""FastAPI observability surface for the OmniPlay-MC brain.

The runnable Mineflayer/Voyager loop is owned by `run_agent.py`. This module
keeps a lightweight HTTP surface for dashboards, health checks, metrics, and
dynamic task injection without depending on the older primitive-action API.

New in this revision
--------------------
- Request-timing middleware: every response carries X-Process-Time-Ms and a
  [timing] log line so dashboard/API bottlenecks are visible immediately.
- GET /metrics — live uptime, cycle count, recent skills, last verdict.
- GET /status  — now pulls currentGoal / currentStatus from the event bus
  rather than returning a mostly static dict.
- POST /prompt — accepts {"task": "..."} and appends to shared task_queue;
  run_agent.py can drain this queue in --interactive mode.
"""

from __future__ import annotations

import os
import time
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, field_validator

from event_bus import default_bus
from models import AgentEventType

LOG = logging.getLogger("omniplay.main")

_NARRATION_DIR = Path(os.getenv("OMNIPLAY_NARRATION_DIR", "outputs/narration"))
_START_TIME = time.time()

# Shared task queue drained by run_agent.py when in --interactive mode.
task_queue: list[str] = []

app = FastAPI(title="OmniPlay-MC AI Brain")

_status: dict[str, Any] = {
    "running": False,
    "currentGoal": None,
    "currentStatus": "idle",
    "cycle": 0,
    "entrypoint": "python -m run_agent",
}


# ---------------------------------------------------------------------------
# Middleware: request timing
# ---------------------------------------------------------------------------

@app.middleware("http")
async def _timing_middleware(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    LOG.info("[timing] %s %s %dms", request.method, request.url.path, elapsed_ms)
    return response


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, Any]:
    """Return readiness for the dashboard/API process."""
    return {
        "brain": "ready",
        "runtime": "external",
        "memory": "local_or_convex",
        "features": {
            "mineflayer_bridge": True,
            "voyager_agents": True,
            "dashboard_ws": True,
            "voice": "optional",
            "interactive_prompt": True,
        },
    }


# ---------------------------------------------------------------------------
# Start / Stop (unchanged semantics, kept for dashboard compatibility)
# ---------------------------------------------------------------------------

@app.post("/start")
async def start(request: dict[str, Any] | None = None) -> dict[str, Any]:
    """Report the supported start path for the current architecture."""
    requested_goal = (request or {}).get("goal") or (request or {}).get("task")
    if requested_goal:
        _status["currentGoal"] = requested_goal
    _status["currentStatus"] = "use run_agent.py to start the Mineflayer loop"
    return {
        "accepted": False,
        "reason": (
            "Start the current main-branch loop with "
            "`python -m run_agent --demo` or `python -m run_agent --task ...` "
            "or `python -m run_agent --interactive`."
        ),
        "status": _status,
    }


@app.post("/stop")
async def stop() -> dict[str, Any]:
    """Mark the API status idle; `run_agent.py` owns real loop shutdown."""
    _status.update({"running": False, "currentStatus": "idle"})
    return {"stopped": True, "status": _status}


# ---------------------------------------------------------------------------
# Status — live from event bus
# ---------------------------------------------------------------------------

@app.get("/status")
async def status() -> dict[str, Any]:
    """Return live agent status derived from the event bus."""
    recent = default_bus().recent(limit=50)

    current_goal: str | None = _status.get("currentGoal")
    current_status: str = _status.get("currentStatus", "idle")
    cycle = 0

    for event in reversed(recent):
        etype = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)

        if current_goal is None and etype == AgentEventType.GOAL_RECEIVED:
            current_goal = event.data.get("task") or event.data.get("goal")

        if etype == AgentEventType.ACTION_STARTED:
            current_status = "executing"
        elif etype == AgentEventType.VERIFICATION_COMPLETED:
            verdict = event.data.get("verdict", "")
            current_status = f"verified:{verdict}"
        elif etype == AgentEventType.PLAN_CREATED:
            current_status = "planning"
        elif etype == AgentEventType.WORLD_OBSERVED:
            current_status = "observing"

        if event.cycle and event.cycle > cycle:
            cycle = event.cycle

    return {
        "running": _status.get("running", False),
        "currentGoal": current_goal,
        "currentStatus": current_status,
        "cycle": cycle,
        "entrypoint": _status.get("entrypoint"),
        "event_count": len(recent),
    }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@app.get("/metrics")
async def metrics() -> dict[str, Any]:
    """Live metrics: uptime, cycle count, recent skills, last verdict."""
    recent = default_bus().recent(limit=256)

    uptime = int(time.time() - _START_TIME)
    total_cycles = 0
    last_verdict: str | None = None
    last_cycle_ms: int | None = None
    recent_skills: list[str] = []

    for event in recent:
        etype = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)

        if event.cycle and event.cycle > total_cycles:
            total_cycles = event.cycle

        if etype == AgentEventType.VERIFICATION_COMPLETED:
            last_verdict = event.data.get("verdict")

        if etype in {AgentEventType.SKILL_CANDIDATE_CREATED, AgentEventType.SKILL_PROMOTED}:
            skill_name = event.data.get("skill") or event.data.get("name")
            if skill_name and skill_name not in recent_skills:
                recent_skills.append(skill_name)

        if etype == AgentEventType.ACTION_COMPLETED:
            wall_ms = event.data.get("wallMs") or event.data.get("durationMs")
            if wall_ms is not None:
                last_cycle_ms = int(wall_ms)

    return {
        "uptime_seconds": uptime,
        "total_cycles": total_cycles,
        "recent_skills": recent_skills[-5:],
        "last_verdict": last_verdict,
        "last_cycle_ms": last_cycle_ms,
        "queued_tasks": len(task_queue),
    }


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

@app.get("/memory")
async def memory() -> dict[str, object]:
    """Return recent in-process Agent Events for dashboard consumers."""
    events = [event.model_dump(mode="json") for event in default_bus().recent()]
    skills = [
        event.data["skill"]
        for event in default_bus().recent()
        if event.event_type.value in {"skill_candidate_created", "skill_promoted"}
        and "skill" in event.data
    ]
    return {
        "events": events,
        "skills": skills,
        "event_count": len(events),
    }


# ---------------------------------------------------------------------------
# Dynamic task injection — POST /prompt
# ---------------------------------------------------------------------------

class PromptRequest(BaseModel):
    task: str

    @field_validator("task")
    @classmethod
    def task_must_be_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("task must be a non-empty string")
        return v.strip()


@app.post("/prompt")
async def prompt(body: PromptRequest) -> dict[str, Any]:
    """Append a task to the shared queue for --interactive mode.

    Example::

        curl -X POST http://localhost:8000/prompt \\
             -H 'Content-Type: application/json' \\
             -d '{"task": "build a dirt house"}'
    """
    task_queue.append(body.task)
    LOG.info("[prompt] queued task #%d: %r", len(task_queue), body.task)
    return {
        "accepted": True,
        "task": body.task,
        "queued_position": len(task_queue),
    }


# ---------------------------------------------------------------------------
# Narration file serving
# ---------------------------------------------------------------------------

@app.get("/narration/{clip_id}")
async def serve_narration(clip_id: str) -> FileResponse:
    """Serve a rendered narration MP3 so the dashboard NarrationPlayer can autoplay."""
    safe_id = "".join(c for c in clip_id if c.isalnum() or c in "-_")
    path = _NARRATION_DIR / f"{safe_id}.mp3"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"clip {safe_id} not found")
    return FileResponse(path, media_type="audio/mpeg")


# ---------------------------------------------------------------------------
# WebSocket event stream
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_events(websocket: WebSocket) -> None:
    """Stream Agent Events to a local dashboard."""
    await websocket.accept()
    try:
        for event in default_bus().recent():
            await websocket.send_json(event.model_dump(mode="json"))
        async with default_bus().subscribe() as queue:
            while True:
                event = await queue.get()
                await websocket.send_json(event.model_dump(mode="json"))
    except WebSocketDisconnect:
        return
