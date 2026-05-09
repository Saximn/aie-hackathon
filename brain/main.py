"""FastAPI entrypoint for the OmniForge AI Brain."""

from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket

from agent_loop import AgentLoop
from event_bus import EventBus
from executor import Executor
from models import (
    AgentLoopStatus,
    BrainHealth,
    ExecutionResult,
    PrimitiveAction,
    RecoveryTransition,
    StartAgentLoopRequest,
    StartAgentLoopResponse,
    StopAgentLoopResponse,
    TrackStatus,
)
from validator import Validator

app = FastAPI(title="OmniForge AI Brain")
_event_bus = EventBus()
_active_loop: AgentLoop | None = None
_run_task: asyncio.Task | None = None

_status = AgentLoopStatus(
    running=False,
    tracks={
        "runtime": TrackStatus.UNKNOWN,
        "observation": TrackStatus.UNKNOWN,
        "planning": TrackStatus.READY,
        "research": TrackStatus.READY,
        "memory": TrackStatus.UNKNOWN,
    },
)


@app.get("/health")
async def health() -> BrainHealth:
    """Return Brain readiness without starting the AgentLoop."""
    return BrainHealth(
        brain=TrackStatus.READY,
        runtime=_status.tracks.get("runtime", TrackStatus.UNKNOWN),
        memory=_status.tracks.get("memory", TrackStatus.UNKNOWN),
        features={
            "game_profiles": True,
            "research": True,
            "voice": False,
            "dashboard_ws": True,
        },
    )


@app.post("/start")
async def start(request: StartAgentLoopRequest) -> StartAgentLoopResponse:
    """Accept an AgentLoop start request and start demo orchestration."""
    global _active_loop, _event_bus, _run_task, _status
    _event_bus = EventBus()
    _active_loop = AgentLoop(
        game=request.game,
        goal=request.goal,
        user_constraints=request.user_constraints,
        max_cycles=request.max_cycles,
        research_allowed=request.research_allowed,
        event_bus=_event_bus,
    )
    _status = AgentLoopStatus(
        running=True,
        game=request.game,
        goal=request.goal,
        cycle=0,
        tracks={
            "runtime": TrackStatus.UNKNOWN,
            "observation": TrackStatus.UNKNOWN,
            "planning": TrackStatus.READY,
            "research": TrackStatus.READY if request.research_allowed else TrackStatus.UNAVAILABLE,
            "memory": TrackStatus.UNKNOWN,
        },
    )
    _run_task = asyncio.create_task(_run_active_loop())
    return StartAgentLoopResponse(accepted=True, status=_status)


@app.post("/stop")
async def stop() -> StopAgentLoopResponse:
    """Stop the local AgentLoop state if it is running."""
    global _run_task, _status
    if _run_task and not _run_task.done():
        _run_task.cancel()
    _status = _status.model_copy(update={"running": False})
    return StopAgentLoopResponse(stopped=True, status=_status)


@app.get("/status")
async def status() -> AgentLoopStatus:
    """Return the current AgentLoop lifecycle status."""
    if _active_loop is not None:
        return _active_loop.status.model_copy(update={"running": _status.running})
    return _status


@app.get("/memory")
async def memory() -> dict[str, object]:
    """Return read-only local Brain memory for the demo dashboard."""
    events = [event.model_dump(mode="json") for event in _event_bus.events]
    skills = [
        event.data["skill"]
        for event in _event_bus.events
        if event.event_type == "skill_candidate_created" and "skill" in event.data
    ]
    return {
        "events": events,
        "skills": skills,
        "event_count": len(events),
    }


@app.post("/test_action")
async def test_action(action: PrimitiveAction) -> ExecutionResult:
    """Validate and send one Primitive Action through the Runtime boundary."""
    validation = Validator().validate_action(action)
    if validation.status != RecoveryTransition.CONTINUE:
        return ExecutionResult(
            action_id=action.id,
            success=False,
            result=validation.reason,
            evidence={"validation": "failed"},
        )
    return await Executor().execute(action)


@app.websocket("/ws")
async def websocket_events(websocket: WebSocket) -> None:
    """Stream Agent Events to a local dashboard."""
    await websocket.accept()
    sent = 0
    try:
        while True:
            events = _event_bus.events
            for event in events[sent:]:
                await websocket.send_json(event.model_dump(mode="json"))
            sent = len(events)
            await asyncio.sleep(0.5)
    except Exception:
        await websocket.close()


async def _run_active_loop() -> None:
    global _status
    if _active_loop is None:
        return

    try:
        while _active_loop.status.running and _active_loop.status.cycle < _active_loop.max_cycles:
            await _active_loop.run_once()
        _status = _active_loop.status.model_copy(update={"running": False})
    except asyncio.CancelledError:
        _status = _status.model_copy(update={"running": False})
    except Exception:
        tracks = dict(_status.tracks)
        tracks["planning"] = TrackStatus.DEGRADED
        _status = _status.model_copy(update={"running": False, "tracks": tracks})
