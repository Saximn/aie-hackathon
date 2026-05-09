# SkillForge Mineflayer Runtime

Person A owns this package. It is the Minecraft-facing runtime: Mineflayer connection, world perception, primitive action execution, screenshots, and seeded runtime skills.

## Contract

The runtime exposes these endpoints for the AI Brain:

- `GET /health`
- `GET /state`
- `GET /screenshot`
- `GET /actions`
- `POST /action`

The runtime should never receive vague goals like "survive the night". It receives one validated `PrimitiveAction` at a time and returns an `ExecutionResult`.

## Scaffold Status

This directory is intentionally scaffold-only. Fill in Mineflayer, HTTP server, and action implementations after the contracts are stable.
