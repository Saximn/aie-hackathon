# Day 1 Smoke Test — Voyager Loop on GPT-5.5

Run after Day 1 work is complete. Each step has the expected pass criterion.

## Prereqs

- Minecraft Java 1.20.4 + Fabric server installed (see [setup_minecraft.md](setup_minecraft.md)).
- `OPENAI_API_KEY` set in `.env` (or environment).
- `bot/node_modules` installed (`cd bot && npm install`).
- `.venv` activated and `pip install -r brain/requirements.txt` run.

## Steps

### 1. Bridge boots and pings

```
cd bot
echo '{"id":"1","method":"ping"}' | npx tsx src/main.ts
```

Pass: stdout contains `{"id":"1","ok":true,"result":{"pong":true}}`.

### 2. Server reachable

In one terminal:

```
scripts\start_server.bat
```

Wait for `Done (X.XXXs)! For help, type "help"`.

### 3. Brain connects, runs one cycle

In another terminal:

```
.venv\Scripts\activate
python brain\run_agent.py --task "chop a tree and collect 1 oak_log" --log-level INFO
```

Pass criteria:

- Log line `mineflayer connected to localhost:25565 as Voyager`.
- Log line `chroma skill count at boot: 0`.
- A series of `omniplay.agent_loop` events: `GOAL_RECEIVED`, `WORLD_OBSERVED`, `MEMORY_RETRIEVED`, `PLAN_CREATED`, `ACTION_STARTED`, `ACTION_COMPLETED`, `VERIFICATION_COMPLETED`.
- One of two end states:
  - On success: `SKILL_PROMOTED` event and `episode done: {... 'skills': 1, ...}`.
  - On failure: clean retry (up to 3 attempts) with structured `FAILURE_DIAGNOSED` events.

### 4. Cross-session persistence

```
python brain\run_agent.py --task "chop a tree" --log-level INFO
```

Pass: `chroma skill count at boot: >= 1`. (After Day 2 with Convex wired, this also pulls cloud skills.)

### 5. Local memory inspection

`brain\.omniplay-memory\events.jsonl` should have one row per event when running without Convex. `brain\.chroma\` contains the local skill embeddings.
