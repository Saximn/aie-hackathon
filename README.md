# OmniPlay-MC (Voyager-Plus)

An observable, self-improving Minecraft AI agent built on **GPT-5.5**, with persistent skill memory, a public live-observability dashboard, and ElevenLabs narration.

> Modernized fork of [MineDojo/Voyager](https://github.com/MineDojo/Voyager): same curriculum / action / critic / skill loop, rebuilt around the OpenAI Responses API + Structured Outputs, the `convex` Python client, and a Next.js 14 dashboard.

## What it does

- Picks the next Minecraft task (curriculum agent), generates a single async JS body to attempt it (action agent), runs it against the live world via Mineflayer, judges the result (critic agent), and stores the working code as a reusable skill.
- Skills persist across sessions in **ChromaDB** (local) and **Convex** (cloud) and are retrieved by semantic similarity for the next task.
- Every agent transition is fanned out to a public **Vercel** dashboard in real time: goal, generated code, verdict, skill library, narration.
- ElevenLabs narrates milestone events (new goal, verdict, skill promoted) without blocking the loop.

## Architecture

```
Local                                      Cloud
─────────────────────────────────────      ────────────────────────
Minecraft Java 1.20.4 client                Convex (events, state,
   │                                          skills, narration)
   │ TCP :25565                                  ▲
   ▼                                             │
Fabric server                                    │
   ▲                                             │
   │ Mineflayer                                  │
bot/  Mineflayer JSON-RPC bridge ◀──── stdio ───▶│
   │  (prismarine-viewer :3007)                  │
   │                                             │
brain/  AgentLoop (Python)                       │
   ├── voyager_agents (curriculum/action/        │
   │     critic/skill) on GPT-5.5                │
   ├── ChromaDB skill vectors                    │
   ├── ElevenLabs narrator (fire-and-forget) ────┘
   └── observability_hook
                                                Vercel
                                                  │
                                              dashboard/  Next.js 14
                                                  - BotView (top-down)
                                                  - GoalPanel
                                                  - EventFeed
                                                  - SkillLibrary
                                                  - NarrationPlayer
```

Two-process runtime:
1. `bot/` — Node.js Mineflayer bridge (`npm run bridge`). Spawned by the brain.
2. `brain/` — Python agent (`python -m brain.run_agent --task "…"` or `--demo`).

## Quickstart

### 1. Minecraft + Fabric

Follow [`scripts/setup_minecraft.md`](scripts/setup_minecraft.md). Then:

```
scripts\start_server.bat
```

### 2. Bot bridge

```
cd bot
npm install
```

The brain auto-spawns the bridge; you don't run it directly.

### 3. Convex backend (cloud, optional but expected for the demo)

```
npx convex dev
```

This logs you in, creates a deployment, watches `convex/`, and prints the URL. Put it in `.env` as `CONVEX_URL` and in `dashboard/.env.local` as `NEXT_PUBLIC_CONVEX_URL`.

### 4. Brain

```
python -m venv .venv
.venv\Scripts\activate
pip install -r brain/requirements.txt
copy .env.example .env   # fill in OPENAI_API_KEY (and ELEVENLABS_API_KEY, CONVEX_URL)
```

### 5. Dashboard

```
cd dashboard
npm install
copy .env.example .env.local   # set NEXT_PUBLIC_CONVEX_URL
npm run dev
```

Open http://localhost:3000.

### 6. Run the agent

Single task:

```
python brain\run_agent.py --task "chop a tree and collect 1 oak_log"
```

Demo curriculum (recommended for the recording):

```
python brain\run_agent.py --demo
```

LLM curriculum (let GPT-5.5 propose tasks):

```
python brain\run_agent.py --curriculum
```

## Repo layout

| Path | Purpose |
| --- | --- |
| `bot/` | Mineflayer JSON-RPC bridge (TypeScript). |
| `brain/` | Python AgentLoop, vendored Voyager agents, Convex + Chroma stores, narrator. |
| `convex/` | Convex schema and mutation/query files. |
| `dashboard/` | Next.js 14 (App Router) live dashboard. |
| `scripts/` | Setup, smoke, demo, and skill-seeding utilities. |
| `tests/` | Offline unit + smoke tests (e.g. cross-session skill persistence). |
| `docs/legacy/` | Quarantined OmniForge scaffold (typed-primitive HTTP server, hand-coded skills) preserved for reference; not in the build path. |

## Verification

Before the demo, run [`scripts/smoke_day1.md`](scripts/smoke_day1.md) end to end. The full demo runbook is [`scripts/demo_runbook.md`](scripts/demo_runbook.md).

## Prize alignment

- **OpenAI / Codex — Best use of GPT-5.5**: GPT-5.5 drives curriculum, code generation, and critic, all via the Responses API + Structured Outputs in `brain/llm_client.py`.
- **Adaption Labs**: cross-session skill memory with retrieval-augmented action prompts, mirrored to Convex for cross-machine reuse.

## Non-goals

- No general-game framework (this is Minecraft-only).
- No VLM / screenshot perception path; symbolic state from Mineflayer is sufficient.
- No fine-tuning; no multi-agent coordination.

See `CONTEXT.md` for terminology and the full event taxonomy.
