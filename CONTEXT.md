# SkillForge

SkillForge is a knowledge-augmented Minecraft survival agent that learns executable survival procedures from observation, failure, retrieved knowledge, and long-term memory.

## Language

**AgentLoop**:
The orchestrator that owns sequencing, retries, replanning, research decisions, memory updates, and event emission for a survival attempt.
_Avoid_: agent, controller, brain

**Observer**:
The module that turns Mineflayer and world state into a structured world snapshot.

**Planner**:
The module that turns a goal, world snapshot, and memory context into a structured plan.

**Executor**:
The module that maps structured actions to Mineflayer commands and reports execution results.

**Validator**:
The module that rejects unsupported, vague, or malformed plans before execution.

**Verifier**:
The module that decides whether an action or plan succeeded from post-action state.

**Diagnoser**:
The module that classifies the likely cause of a failed action or plan.

**Verification Status**:
The observable outcome of a Primitive Action or Plan as determined from post-action state.
_Avoid_: error, result

**Failure Type**:
The diagnosed reason a non-successful Verification Status occurred.
_Avoid_: exception, bug

**Recovery Transition**:
The AgentLoop decision made after verification and diagnosis, such as continue, retry, replan, research, abort, or store memory.
_Avoid_: fallback

**RecoveryPolicy**:
The module that maps verification and diagnosis into the next recovery transition.

**Researcher**:
The module that retrieves external survival knowledge when the AgentLoop determines the agent is missing a strategy.
_Avoid_: Exa, search

**SkillBuilder**:
The module that converts retrieved survival guidance into reusable executable skills.

**Skill**:
A versioned structured procedure that captures reusable survival knowledge for planning without containing executable code.
_Avoid_: script, plugin, macro

**Plan**:
An ephemeral grounded action sequence for a specific goal and world snapshot.
_Avoid_: strategy, recipe

**Primitive Action**:
An atomic Minecraft bot operation that the Executor can run through Mineflayer.
_Avoid_: command, skill step

**MemoryStore**:
The module that persists learned skills, failures, and user preferences for future survival attempts.
_Avoid_: Hyperspell, Convex

**Dashboard Event**:
A structured real-time record emitted by the AgentLoop so the dashboard can show state, reasoning, actions, verification, diagnosis, research, and learned skills.
_Avoid_: log line

**WorldSnapshot**:
The structured state object derived from Mineflayer perception and used as the only state input for planning and verification.
_Avoid_: raw bot state

**ExecutionResult**:
The structured result returned after a Primitive Action is attempted by the Mineflayer runtime.

**Diagnosis**:
The structured output from the Diagnoser describing why a non-successful Verification Status occurred.

## Relationships

- The **AgentLoop** calls **Observer**, **Planner**, **Executor**, **Verifier**, **Diagnoser**, **Researcher**, **SkillBuilder**, and **MemoryStore**.
- **Observer**, **Planner**, **Executor**, **Verifier**, **Diagnoser**, **Researcher**, **SkillBuilder**, and **MemoryStore** return structured results and do not call each other directly.
- The **AgentLoop** emits one or more **Dashboard Events** for every orchestration step.
- The **Validator** rejects unsupported, vague, or malformed **Plans** before the **Executor** can act.
- The **Researcher** retrieves external knowledge only when the **AgentLoop** decides the current failure requires missing survival strategy.
- The **MemoryStore** persists successful skills, failed attempts, and user preferences when directed by the **AgentLoop**.
- A **Skill** contains a goal, preconditions, ordered primitive action templates, success criteria, failure modes, source, confidence, and verification metadata.
- The **Planner** may use **Skills** as reusable planning knowledge, but the **Executor** only runs **Primitive Actions**.
- A **Plan** may reference the **Skills** used to derive it, but every executable step in a **Plan** must be a grounded **Primitive Action**.
- A **Plan** is invalid unless every **Primitive Action** has explicit arguments, expected result, timeout, and failure policy.
- The **Executor** validates and runs known **Primitive Action** types; it does not interpret abstract survival-language steps.
- The **Verifier** reports a **Verification Status** from observable post-action state.
- The **Diagnoser** refines non-successful outcomes into a **Failure Type**.
- The **RecoveryPolicy** maps a **Verification Status** and **Failure Type** into a **Recovery Transition**.
- The **AgentLoop** owns the final transition decision and may apply or override the **RecoveryPolicy** result.
- **Verification Status** values include success, incomplete, failed, stuck, unsafe, and invalid plan.
- **Failure Type** values include missing prerequisite, insufficient resources, resource unavailable, pathfinding failure, crafting failure, combat risk, environment changed, bad plan ordering, ambiguous action, unsupported action, missing strategy, and timeout.
- **WorldSnapshot**, **Primitive Action**, **Plan**, **ExecutionResult**, **Verification Status**, **Diagnosis**, **Skill**, and **Dashboard Event** are shared contracts between modules.

## Example dialogue

> **Dev:** "Should the Diagnoser call Exa when it thinks the shelter strategy is weak?"
> **Domain expert:** "No. The **Diagnoser** returns a structured diagnosis; the **AgentLoop** decides whether to call the **Researcher**."

> **Dev:** "Can a retrieved shelter guide become a script that the bot runs?"
> **Domain expert:** "No. It can become a **Skill**, but the **Executor** only runs validated **Primitive Actions** through Mineflayer."

> **Dev:** "Can the Planner send 'build a shelter' to the Executor?"
> **Domain expert:** "No. The **Planner** must compile that into grounded **Primitive Actions** with concrete arguments and success criteria before execution."

> **Dev:** "If collecting twelve logs times out with seven logs, who decides what happens next?"
> **Domain expert:** "The **Verifier** reports incomplete, the **Diagnoser** classifies the **Failure Type**, and the **AgentLoop** chooses the **Recovery Transition**."

## System Design

SkillForge is split into a **Mineflayer Runtime** and an **AI Brain**.

```text
Mineflayer perceptions
-> WorldSnapshot
-> Planner
-> grounded Primitive Action
-> Validator
-> Executor
-> Mineflayer action
-> post-action WorldSnapshot
-> Verifier
-> Diagnoser
-> RecoveryPolicy
-> memory and skill update
-> Dashboard Event stream
```

The LLM never controls Mineflayer directly. It proposes structured plans, and SkillForge validates, executes, verifies, diagnoses, and learns from them.

## Ownership

**Person A - Mineflayer Runtime**:
Owns `bot/`, including Mineflayer connection, perception extraction, screenshots, primitive action handlers, and seeded runtime skills.

**Person B - AI Brain**:
Owns `brain/`, including AgentLoop orchestration, planning, action validation, verification, diagnosis, recovery policy, research, skill building, memory, dashboard events, voice, and imagined futures.

## Shared HTTP Contract

The Mineflayer Runtime exposes:

- `GET /health`: runtime health and bot liveness
- `GET /state`: current perception state
- `GET /screenshot`: current first-person PNG screenshot
- `GET /actions`: supported primitive action and seeded skill metadata
- `POST /action`: executes one grounded Primitive Action

The AI Brain exposes:

- `GET /health`: brain, bot, memory, and feature-flag health
- `POST /start`: starts the AgentLoop
- `POST /stop`: stops the AgentLoop
- `GET /status`: current cycle, goal, transition, and track status
- `GET /memory`: current memory and skill state
- `POST /test_action`: validates and sends one Primitive Action
- `WS /ws`: streams Dashboard Events

## Module Scaffolds

`bot/` contains the TypeScript Mineflayer runtime scaffold:

- `main.ts`: runtime entrypoint
- `routes.ts`: HTTP routes
- `perception.ts`: Mineflayer state to perception object
- `actionRegistry.ts`: supported action metadata and serialization
- `actionExecutor.ts`: primitive action execution boundary
- `types.ts`: shared TypeScript contracts
- `skills/`: seeded runtime skill stubs

`brain/` contains the Python AI Brain scaffold:

- `main.py`: FastAPI entrypoint
- `agent_loop.py`: orchestration loop
- `models.py`: shared Pydantic contracts and enums
- `bot_client.py`: HTTP client for the Mineflayer Runtime
- `observer.py`: perception to WorldSnapshot
- `planner.py`: GPT-5.5 structured planner
- `validator.py`: plan and action validation
- `executor.py`: action dispatch to BotClient
- `verifier.py`: expected result checks
- `diagnoser.py`: failure classification
- `recovery_policy.py`: transition recommendation
- `researcher.py`: external knowledge retrieval
- `skill_builder.py`: skill creation and update
- `memory_store.py`: Convex primary memory with JSON fallback
- `event_bus.py`: Dashboard Event broadcast
- `imagine.py`: imagined future image generation
- `voice.py`: optional event narration

## Flagged ambiguities

- "agent" can mean the whole SkillForge system or the orchestration loop; resolved: use **AgentLoop** for orchestration and SkillForge for the whole system.
