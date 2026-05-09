"""FastAPI entrypoint scaffold for the OmniForge AI Brain."""

from fastapi import FastAPI

from models import (
    AgentLoopStatus,
    BrainHealth,
    StartAgentLoopRequest,
    StartAgentLoopResponse,
    StopAgentLoopResponse,
    TrackStatus,
)

app = FastAPI(title="OmniForge AI Brain")

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
            "dashboard_ws": False,
        },
    )


@app.post("/start")
async def start(request: StartAgentLoopRequest) -> StartAgentLoopResponse:
    """Accept an AgentLoop start request.

    Full background execution will attach here later. The contract already
    gives callers a stable status shape for dashboards and tests.
    """
    global _status
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
    return StartAgentLoopResponse(accepted=True, status=_status)


@app.post("/stop")
async def stop() -> StopAgentLoopResponse:
    """Stop the local AgentLoop state if it is running."""
    global _status
    _status = _status.model_copy(update={"running": False})
    return StopAgentLoopResponse(stopped=True, status=_status)


@app.get("/status")
async def status() -> AgentLoopStatus:
    """Return the current AgentLoop lifecycle status."""
    return _status
