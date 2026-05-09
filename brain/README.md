# SkillForge AI Brain

Person B owns this package. It orchestrates the AgentLoop, planning, validation, execution dispatch, verification, diagnosis, recovery policy, research, skill learning, memory, and dashboard events.

## Contract

The brain consumes the Mineflayer Runtime API:

- `GET /health`
- `GET /state`
- `GET /screenshot`
- `GET /actions`
- `POST /action`

The brain exposes:

- `GET /health`
- `POST /start`
- `POST /stop`
- `GET /status`
- `GET /memory`
- `POST /test_action`
- `WS /ws`

## Scaffold Status

This directory is intentionally scaffold-only. Implement the core AgentLoop before adding Convex, Exa, image generation, or voice.
