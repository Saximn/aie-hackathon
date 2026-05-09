# OmniPlay-MC (Voyager-Plus)

OmniPlay-MC is an observable, self-improving Minecraft agent. It is a modernized fork of [MineDojo/Voyager](https://github.com/MineDojo/Voyager) rebuilt around GPT-5.5, Convex live store, ChromaDB skill memory, and a Next.js public dashboard.

One-line pitch:

> OmniPlay-MC plays Minecraft by asking GPT-5.5 to write JavaScript, runs that JS through a Mineflayer bridge, judges the result, and saves the working code as a reusable skill — then streams every step to a public live-observability dashboard.

## Scope

- **Game**: Minecraft Java 1.20.4 (Fabric server, online-mode false). Not framework-agnostic; not a multi-game claim.
- **Perception**: symbolic-only. We read inventory, position, biome, nearby blocks, and entities from Mineflayer. No screenshots; no VLM.
- **Action**: code-as-policy. The action agent emits an async JS body that runs inside the Mineflayer bridge with `(bot, mcData, Vec3, goals, Movements)` in scope.
- **Memory**: ChromaDB locally + Convex in the cloud. Skills survive restart and machine moves.

## Architecture

```
Local                                            Cloud
─────────────────────────────────────────────    ─────────────────────────
Minecraft Java 1.20.4                            Convex
   │                                              ├ episodes
Fabric server :25565                              ├ events
   │                                              ├ current_state
bot/  Mineflayer JSON-RPC bridge ◀──── stdio ─────┤  ▲
   ├ voyagerBridge.ts                              │  │
   ├ skillPrimitives.ts                            │  │
   └ viewer.ts (prismarine, :3007 best-effort)     │  │
   │                                              ├ skills
brain/  AgentLoop                                 ├ narration_clips
   ├ voyager_agents/                              └ lessons
   │   ├ curriculum.py                                ▲
   │   ├ action.py                                    │
   │   ├ critic.py                                    │
   │   └ skill.py (ChromaDB)                          │
   ├ llm_client.py     (Responses API + Structured Outputs)
   ├ observer.py       (symbolic only)
   ├ executor.py       (JS via bridge)
   ├ verifier.py       (wraps critic)
   ├ memory_store.py   (Convex client + JSONL fallback)
   ├ event_bus.py      (in-process pub/sub)
   ├ observability_hook.py
   └ voice.py          (ElevenLabs, fire-and-forget)

dashboard/  Next.js 14 app                       Vercel
   ├ BotView                                       (deploys dashboard,
   ├ GoalPanel                                      reads Convex via
   ├ EventFeed                                      NEXT_PUBLIC_CONVEX_URL)
   ├ SkillLibrary
   └ NarrationPlayer
```

## Demo flow

1. Curriculum agent picks the next task (or the demo curriculum hardcoded list).
2. Observer queries `bridge.getState()` → `WorldSnapshot`.
3. SkillManager retrieves the top-3 most relevant prior skills via embedding similarity.
4. Action agent emits `{ explain, plan, code, name }`.
5. Validator rejects forbidden tokens (require, fs, eval, etc.).
6. Executor runs `bridge.runJs(code)`. The bridge wraps it in `(async (bot, mcData, Vec3, goals, Movements) => { ... })()` and captures result/error/timeout.
7. Observer takes a fresh `WorldSnapshot`.
8. Critic agent compares before/after → `{verdict, confidence, feedback}`.
9. On success: SkillBuilder writes the JS to Chroma + Convex; emit `skill_promoted`. On failure: retry up to 3 attempts, feeding the previous error back to the action prompt.
10. Every transition is mirrored to Convex `events` and broadcast on the local event bus.

## Language

- **AgentLoop**: the orchestrator (`brain/agent_loop.py`). Runs `run_once(task)` and `run_episode(task_queue, max_cycles, use_curriculum)`.
- **CurriculumAgent**: GPT-5.5 component that proposes the next task. Lives in `brain/voyager_agents/curriculum.py`.
- **ActionAgent**: GPT-5.5 component that emits an async JS body. Lives in `brain/voyager_agents/action.py`.
- **CriticAgent**: GPT-5.5 component that judges success. Lives in `brain/voyager_agents/critic.py`.
- **SkillManager**: ChromaDB-backed skill store with OpenAI-embedded vector retrieval. Lives in `brain/voyager_agents/skill.py`.
- **JsCodeAction**: the unit emitted by the action agent and consumed by the executor. `(id, name, description, code, expected_outcome, timeout_ms)`.
- **BotClient**: the brain's stdin/stdout client to the bridge. Methods: `start, connect, run_js, get_state, chat, ping, stop`.
- **VoyagerBridge**: the Node.js JSON-RPC server in `bot/`. Same method names. Stdout is reserved for protocol; stderr is human logs.
- **Sandbox**: the `(bot, mcData, Vec3, goals, Movements)` tuple given to generated JS (`bot/src/skillPrimitives.ts::buildSandbox`).
- **WorldSnapshot**: structured input to planning and verification; preserved from OmniForge so dashboard fields don't shift. Visual fields default to `unknown`.
- **AgentEvent**: every state transition is an `AgentEvent`. The taxonomy below is the source of truth for the dashboard and Convex `events.eventType` values.
- **Episode**: the lifetime of one `run_episode`. Identified by `MemoryStore.episode_id`. Convex-side episodes group events, state, and narration clips.
- **NarrationClip**: an ElevenLabs synthesis triggered by an event. `voice.py::Narrator.fire_and_forget`. Mirrored to Convex `narration_clips`.
- **Lesson**: post-mortem text extracted from a failure. Stretch goal; the schema and Convex table exist but the diagnoser only does keyword classification today.

## Agent Event taxonomy

| Event | Emitted when |
| --- | --- |
| `goal_received` | AgentLoop accepts a new task (from queue, curriculum, or `--task`). |
| `world_observed` | Observer produced a fresh WorldSnapshot. |
| `memory_retrieved` | SkillManager retrieved top-K skills for the task. |
| `plan_created` | ActionAgent produced `{explain, plan, code}`; mirrored as a `Plan` for the dashboard. |
| `action_started` / `action_completed` | Bridge `runJs` started / returned (or timed out). |
| `verification_completed` | Critic returned `{verdict, confidence, feedback}`. |
| `failure_diagnosed` | Diagnoser keyword-classified a non-success verdict. |
| `skill_candidate_created` / `skill_promoted` | SkillBuilder wrote a successful skill to Chroma + Convex. |

## Recovery transitions

The `RecoveryPolicy` returns one of:

- `STORE_MEMORY` — success path; SkillBuilder runs.
- `REPLAN` — retry with previous error fed back to the ActionAgent (up to 3 attempts).
- `ABORT` — give up on this task; mark in failed list.

`RESEARCH` and `ASK_USER` exist in the enum but are not wired in this build (out of scope for the hackathon).

## File ownership

- Anything under `bot/` is the Mineflayer runtime: connect, plugin loading, JSON-RPC, optional viewer.
- Anything under `brain/` is the Python AgentLoop and its components.
- Anything under `convex/` is server-side TypeScript: schema, mutations, queries.
- Anything under `dashboard/` is client-side React for the Vercel deployment.
- `docs/legacy/` is quarantined OmniForge code from the previous scaffold (typed-primitive HTTP runtime, hand-coded TS skills, generic-input adapter). Not imported by the active build; preserved for reference.

## Cost ceiling

GPT-5.5 calls are tracked in `llm_client.usage_snapshot()`. The agent caps episodes at `MAX_CYCLES` (default 50) so a single demo stays under ~$5 at $5-in / $30-out per Mtok with `medium` reasoning effort.

## What is intentionally not built

- Generic keyboard/mouse adapter for non-Minecraft games (lives in `docs/legacy/bot/`).
- VLM perception path.
- Multi-agent / MCP / mobile.
- Fine-tuning.
- A real diagnoser. The current one only does keyword classification; an LLM-driven post-mortem is a Day 3 stretch.
