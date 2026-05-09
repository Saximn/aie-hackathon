# OmniForge

OmniForge is a game-agnostic open-world agent architecture, first benchmarked on Minecraft/Minetest.

The current repo state is scaffold-only. It defines contracts, module boundaries, and ownership so two people can implement in parallel without making hidden architecture decisions.

## Pitch

OmniForge learns how to play slow open-world games by researching the game, observing the screen with a VLM, planning grounded primitive actions with GPT-5.5, controlling the game through keyboard/mouse or an optional game adapter, diagnosing failures, and storing reusable skills.

We are building the general architecture for open-world games, with Minecraft/Minetest as the first benchmark. We do not claim OmniForge can play all games.

## Project Split

`brain/` is the Python AI Brain scaffold owned by Person B:

- AgentLoop orchestration
- Game Profile creation
- VLM/world observation boundary
- GPT-5.5 structured planning boundary
- verification, diagnosis, recovery, research, skills, memory, and events

`bot/` is the TypeScript Runtime scaffold owned by Person A:

- generic keyboard/mouse primitive actions
- optional Minecraft/Mineflayer adapter actions
- symbolic state and screenshot boundaries
- runtime HTTP endpoints

## Current Status

This is intentionally not implemented yet. Most methods raise `NotImplementedError` or `TODO` errors.

No virtual environment is included yet. Do not run Python checks until `.venv` or `venv` exists and is activated.

See `CONTEXT.md` for the architecture, language, contracts, event model, and two-person task split.
