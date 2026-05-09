# OmniForge AI Brain

Person B owns this package.

This package contains the runnable local AI Brain demo path for:

- AgentLoop orchestration
- Game profile creation
- VLM/world observation
- deterministic demo planning with a stable seam for GPT-5.5 structured planning
- action validation and dispatch
- verification, diagnosis, and recovery policy
- research hooks
- skill memory
- dashboard events and a local WebSocket stream
- optional voice coaching

Do not put game-specific execution logic here. The brain sends grounded Primitive Actions to the runtime.

The default demo path is intentionally deterministic and API-key-free:

1. `GameProfileBuilder` loads a static Minecraft or Minetest Game Profile.
2. `Observer` builds a World Snapshot from Runtime state when available, or a low-confidence fallback when no Runtime is attached.
3. `Planner` produces grounded Primitive Actions for the first-night demo.
4. `AgentLoop` validates, executes, verifies, diagnoses, optionally researches, and emits Agent Events.
5. `MemoryStore` can persist events, Research Notes, Game Profiles, and Skills when Hyperspell is configured.

Optional voice coaching and image generation remain sponsor-track stubs.
