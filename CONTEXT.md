# OmniForge

OmniForge is a game-agnostic open-world agent architecture, first benchmarked on Minecraft/Minetest.

One-line pitch:

OmniForge learns how to play slow open-world games by researching the game, observing the screen with a VLM, planning grounded primitive actions with GPT-5.5, controlling the game through keyboard/mouse or an optional game adapter, diagnosing failures, and storing reusable skills.

Important claim boundary:

We are building the general architecture for open-world games, with Minecraft/Minetest as the first benchmark. We do not claim OmniForge can play all games.

## Demo Target

The first demo targets slow open-world survival gameplay where strategic decisions matter more than reflexes.

Primary benchmark goal:

`survive_first_night`

Concrete demo flow:

1. Build or load a Game Profile for Minecraft/Minetest.
2. Capture a screenshot from the game window.
3. Produce a structured World Snapshot from VLM perception and optional symbolic state.
4. Retrieve relevant skills and recent failures from memory.
5. Ask GPT-5.5 to produce a grounded Plan made only of Primitive Actions.
6. Validate and execute the actions through keyboard/mouse or an optional Minecraft adapter.
7. Verify the outcome against each action expected result.
8. Diagnose non-successful outcomes.
9. Accept user coaching by text or voice.
10. Create or update a Skill and retry.

The hackathon demo should avoid fast combat, complex crafting menus, arbitrary exploration, PvP, FPS aiming, precision platforming, and long autonomous runs.

## Language

**OmniForge**:
The overall game-agnostic open-world agent system.
_Avoid_: universal game bot, plays all games

**AgentLoop**:
The orchestrator that owns sequencing, retries, replanning, research decisions, memory updates, and event emission.
_Avoid_: agent, controller, brain

**GameProfileBuilder**:
The module that creates a structured Game Profile from static config or research.
_Avoid_: hardcoded Minecraft assumptions

**Game Profile**:
The structured controls, mechanics, risks, and early objectives for one game.
_Avoid_: guide, wiki dump

**Observer**:
The module that turns screenshot perception and optional symbolic state into a World Snapshot.

**Visual Observation**:
The VLM-derived scene summary, visible objects, risk level, time estimate, UI state, and confidence.

**Symbolic Observation**:
Optional adapter-derived state such as health, hunger, inventory, nearby blocks, position, or biome.

**World Snapshot**:
The structured state object used as the only state input for planning and verification.
_Avoid_: raw bot state

**Planner**:
The GPT-5.5 module that turns a goal, Game Profile, World Snapshot, memory, user constraints, and recent failures into a grounded Plan.

**Plan**:
An ephemeral grounded action sequence for a specific goal and World Snapshot.
_Avoid_: strategy, recipe

**Primitive Action**:
An atomic operation the Executor can run through a universal input adapter or optional game adapter.
_Avoid_: vague command, skill step

**Executor**:
The module that runs allowed Primitive Actions and returns Execution Results. The Executor does not reason and does not interpret natural language.

**Verifier**:
The module that decides whether an action or plan succeeded from post-action screenshot and optional symbolic state.

**Verification Status**:
The observable outcome of a Primitive Action or Plan.
_Avoid_: error, result

**Diagnoser**:
The module that classifies why a non-successful Verification Status occurred.

**Failure Type**:
The diagnosed cause of a non-successful Verification Status.
_Avoid_: exception, bug

**Recovery Transition**:
The AgentLoop decision made after verification and diagnosis: continue, retry, replan, research, abort, store memory, or promote skill.
_Avoid_: fallback

**RecoveryPolicy**:
The module that maps verification and diagnosis into a recommended Recovery Transition.

**Researcher**:
The module that retrieves external game knowledge only when the AgentLoop decides knowledge is missing.
_Avoid_: calling Exa every loop

**SkillBuilder**:
The module that converts successful actions, coaching, or researched guidance into reusable structured Skills.

**Skill**:
A versioned structured procedure that captures reusable play knowledge without containing executable code.
_Avoid_: script, plugin, macro

**MemoryStore**:
The module that persists events, skills, failures, user preferences, and current dashboard state.
_Avoid_: direct Convex/Hyperspell coupling in core logic

**Agent Event**:
A structured real-time record emitted by the AgentLoop so the dashboard can show profile, perception, planning, actions, verification, diagnosis, research, coaching, and learned skills.
_Avoid_: untyped log line

## Relationships

- The **AgentLoop** calls **GameProfileBuilder**, **Observer**, **Planner**, **Executor**, **Verifier**, **Diagnoser**, **Researcher**, **SkillBuilder**, **MemoryStore**, and **RecoveryPolicy**.
- Subcomponents return structured data and do not call each other directly.
- The **AgentLoop** emits one or more **Agent Events** for every orchestration step.
- The **GameProfileBuilder** uses static config first and may call research only when creating or repairing a profile.
- The **Observer** uses VLM screenshot perception as the generic path and optional game-specific symbolic state when available.
- The **Planner** may use Skills as reusable planning knowledge, but every executable step in a Plan must be a grounded Primitive Action.
- The **Executor** runs only supported Primitive Actions. It does not interpret abstract goals such as "survive the night" or "build a shelter".
- The **Verifier** compares post-action state against the expected result attached to the Primitive Action.
- The **Diagnoser** classifies non-successful outcomes and recommends repair, retry, replan, or research.
- The **Researcher** is called only for new Game Profiles, missing strategy, repeated failure, unknown mechanics, or explicit user instruction.
- The **SkillBuilder** creates Skills from successful plans, user coaching, and researched strategies.
- A **Skill** can be promoted from `candidate` to `verified` after one successful execution.
- Convex is the preferred live memory and dashboard store. Local JSON is the fallback. Hyperspell is optional long-term semantic memory.

## Architecture

```text
User / Judge
  -> text or voice coaching
  -> AgentLoop

Game Window
  -> screenshot
  -> VLM Observer
  -> World Snapshot

GameProfileBuilder
  -> static profile or research notes
  -> Game Profile

AgentLoop
  -> retrieve memory
  -> GPT-5.5 Planner
  -> grounded Plan
  -> Validator
  -> Executor
  -> keyboard/mouse adapter or optional Minecraft adapter
  -> Verifier
  -> Diagnoser
  -> RecoveryPolicy
  -> SkillBuilder
  -> MemoryStore
  -> Dashboard Event stream
```

Two-speed loop:

- Slow AI loop: observe, plan, verify, diagnose, repair, update memory.
- Fast control loop: execute keypresses, mouse movement, clicks, waits, and adapter calls locally.

## Primitive Actions

Generic actions:

- `press_key`
- `hold_key`
- `move_mouse`
- `click`
- `wait`
- `open_menu`
- `select_hotbar_slot`
- `move_toward_visible_object`
- `interact_primary`

Optional Minecraft adapter actions:

- `collect_block`
- `craft_item`
- `build_shelter`

The generic path is screenshot plus keyboard/mouse. Game-specific adapters can improve reliability when available.

## Canonical Events

- `goal_received`
- `game_profile_created`
- `world_observed`
- `memory_retrieved`
- `plan_created`
- `action_started`
- `action_completed`
- `verification_completed`
- `failure_diagnosed`
- `research_started`
- `research_completed`
- `skill_candidate_created`
- `skill_promoted`
- `user_instruction_received`

## Shared HTTP Contract

The Runtime exposes:

- `GET /health`: runtime health and adapter liveness
- `GET /state`: optional symbolic game state
- `GET /screenshot`: current first-person PNG screenshot
- `GET /actions`: supported primitive action and adapter action metadata
- `POST /action`: executes one grounded Primitive Action

The AI Brain exposes:

- `GET /health`: brain, runtime, memory, and feature-flag health
- `POST /start`: starts the AgentLoop
- `POST /stop`: stops the AgentLoop
- `GET /status`: current cycle, goal, transition, and track status
- `GET /memory`: current memory and skill state
- `POST /test_action`: validates and sends one Primitive Action
- `WS /ws`: streams Agent Events

## Module Scaffolds

`bot/` contains the TypeScript runtime scaffold:

- `main.ts`: runtime entrypoint
- `routes.ts`: HTTP routes
- `perception.ts`: symbolic state and screenshot boundary
- `actionRegistry.ts`: supported action metadata and validation
- `actionExecutor.ts`: primitive action execution boundary
- `types.ts`: shared TypeScript contracts
- `skills/`: optional seeded game-adapter skill stubs

`brain/` contains the Python AI Brain scaffold:

- `main.py`: FastAPI entrypoint
- `agent_loop.py`: orchestration loop
- `models.py`: shared Pydantic contracts and enums
- `game_profile_builder.py`: static profile and research hook boundary
- `bot_client.py`: HTTP client for the runtime
- `observer.py`: runtime perception and VLM summary to WorldSnapshot
- `planner.py`: GPT-5.5 structured planner boundary
- `validator.py`: plan and action validation
- `executor.py`: action dispatch to BotClient
- `verifier.py`: expected result checks
- `diagnoser.py`: failure classification
- `recovery_policy.py`: transition recommendation
- `researcher.py`: external knowledge retrieval hook
- `skill_builder.py`: skill creation and update
- `memory_store.py`: Convex primary memory with JSON fallback
- `event_bus.py`: Agent Event broadcast
- `voice.py`: optional coaching input and event narration

## Ownership

**Person A - Runtime and Adapter Layer**:
Owns `bot/`. Implements generic keyboard/mouse primitive actions, optional Mineflayer adapter actions, screenshot capture, symbolic state, action execution, and runtime HTTP endpoints.

**Person B - AI Brain and Documentation**:
Owns `brain/` and `CONTEXT.md`. Implements AgentLoop scaffolding, Game Profile creation, observation, planning, verification, diagnosis, research hooks, skill memory, and dashboard events.

## Sponsor Tracks

Primary track:

OpenAI/Codex Best use of GPT-5.5. GPT-5.5 is the reasoning core for planning, verification, diagnosis, repair, user coaching, and skill creation.

Secondary track:

Convex Best use of Convex. Convex powers the real-time memory, dashboard state, action logs, skill table, and failure history.

Optional tracks:

- Gemini voice coaching if voice is implemented.
- Hyperspell long-term semantic memory if integration is quick.
- Exa game profile and strategy research.

## Example Dialogue

> **Dev:** "Can OmniForge claim it plays all games?"
> **Domain expert:** "No. Say it is a general architecture for open-world games, with Minecraft/Minetest as the first benchmark."

> **Dev:** "Can the Planner send 'build shelter' to the Executor?"
> **Domain expert:** "No. The Planner must compile that into grounded Primitive Actions with explicit arguments and expected results."

> **Dev:** "Should the Diagnoser call Exa when it thinks the shelter strategy is weak?"
> **Domain expert:** "No. The Diagnoser returns a structured diagnosis. The AgentLoop decides whether to call the Researcher."

> **Dev:** "Is a Skill executable code?"
> **Domain expert:** "No. A Skill is a versioned structured procedure. The Executor only runs validated Primitive Actions."

## Current Implementation Constraints

- No `.venv` or `venv` exists in the repo, and the current scaffold pass must not create one.
- Command-based tests should wait until a virtual environment exists.
- OpenAI API usage should follow the official Responses API and Structured Outputs guidance.
- Secrets, API keys, tokens, and credentials must never be committed or logged.
