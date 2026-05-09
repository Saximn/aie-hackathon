"""FastAPI entrypoint scaffold for the OmniForge AI Brain."""

from fastapi import FastAPI

app = FastAPI(title="OmniForge AI Brain")


@app.get("/health")
async def health() -> dict[str, str]:
    """TODO(Person B): include runtime, memory, and feature-flag health."""
    return {"brain": "scaffold"}


@app.post("/start")
async def start() -> dict[str, str]:
    """TODO(Person B): start the AgentLoop."""
    raise NotImplementedError("POST /start is scaffold-only")


@app.post("/stop")
async def stop() -> dict[str, str]:
    """TODO(Person B): stop the AgentLoop."""
    raise NotImplementedError("POST /stop is scaffold-only")


@app.get("/status")
async def status() -> dict[str, str]:
    """TODO(Person B): return current loop status."""
    raise NotImplementedError("GET /status is scaffold-only")
