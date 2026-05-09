"""FastAPI observability surface for the OmniPlay-MC brain.

The runnable Mineflayer/Voyager loop is owned by `run_agent.py`. This module
keeps a lightweight HTTP/WS surface for dashboards and health checks without
depending on the older primitive-action API contracts.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from event_bus import default_bus

app = FastAPI(title="OmniPlay-MC AI Brain")
_status: dict[str, Any] = {
    "running": False,
    "currentGoal": None,
    "currentStatus": "idle",
    "cycle": 0,
    "entrypoint": "python -m run_agent",
}


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
        },
    }


@app.post("/start")
async def start(request: dict[str, Any] | None = None) -> dict[str, Any]:
    """Report the supported start path for the current architecture."""
    requested_goal = (request or {}).get("goal") or (request or {}).get("task")
    if requested_goal:
        _status["currentGoal"] = requested_goal
    _status["currentStatus"] = "use run_agent.py to start the Mineflayer loop"
    return {
        "accepted": False,
        "reason": "Start the current main-branch loop with `python -m run_agent --demo` or `python -m run_agent --task ...`.",
        "status": _status,
    }


@app.post("/stop")
async def stop() -> dict[str, Any]:
    """Mark the API status idle; `run_agent.py` owns real loop shutdown."""
    _status.update({"running": False, "currentStatus": "idle"})
    return {"stopped": True, "status": _status}


@app.get("/status")
async def status() -> dict[str, Any]:
    """Return the last known dashboard/API status."""
    return _status


@app.get("/memory")
async def memory() -> dict[str, object]:
    """Return recent in-process Agent Events for dashboard consumers."""
    events = [event.model_dump(mode="json") for event in default_bus().recent()]
    skills = [
        event.data["skill"]
        for event in default_bus().recent()
        if event.event_type.value in {"skill_candidate_created", "skill_promoted"} and "skill" in event.data
    ]
    return {
        "events": events,
        "skills": skills,
        "event_count": len(events),
    }


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
