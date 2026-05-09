"""FastAPI entrypoint for the SkillForge AI Brain."""

from fastapi import FastAPI

app = FastAPI(title="SkillForge AI Brain")


@app.get("/health")
async def health() -> dict[str, str]:
    """Return scaffold health.

    TODO(Person B): include bot, memory, feature flag, and loop health.
    """
    return {"brain": "scaffold"}
