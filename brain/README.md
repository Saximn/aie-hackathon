# OmniPlay-MC AI Brain

Python package that owns the agent loop, memory, and observability surface for OmniPlay-MC.

## Architecture

```
run_agent.py           — CLI entrypoint (start here)
agent_loop.py          — Voyager-Plus orchestration loop
  observer.py          — WorldSnapshot from Mineflayer symbolic state
  planner.py           — JsCodeAction generation via ActionAgent (GPT-5.5)
  executor.py          — dispatches JsCodeAction to BotClient over stdin/stdout
  verifier.py          — maps critic verdict → VerificationResult
  diagnoser.py         — keyword-based failure classification + lesson writing
  recovery_policy.py   — VerificationStatus → RecoveryTransition state machine
bot_client.py          — spawns the Mineflayer bridge subprocess (npx tsx)
skill_builder.py       — creates SkillRecord from a verified run → ChromaDB
memory_store.py        — Convex-backed persistence with local JSONL fallback
voice.py               — ElevenLabs TTS, fire-and-forget on a thread pool
main.py                — FastAPI observability surface (health, status, /ws, /narration)
event_bus.py           — in-process pub/sub for AgentEvent
```

## Running the agent

```powershell
# Activate the venv first
. .venv\Scripts\Activate.ps1

# Run the canned demo curriculum
python brain\run_agent.py --demo --log-level INFO

# Run a single task
python brain\run_agent.py --task "chop a tree and collect 4 oak_log"

# Use the GPT-5.5 curriculum agent for open-ended play
python brain\run_agent.py --curriculum
```

The FastAPI observability surface starts separately (for the dashboard):

```powershell
uvicorn brain.main:app --reload --port 8000
```

## Key contracts

**Input to the loop:** `WorldSnapshot` (built by `observer.py` from Mineflayer symbolic state)

**Output from the loop:** `JsCodeAction` (JavaScript executed in the Mineflayer sandbox via the bot bridge)

**Verification:** Critic LLM verdict → `VerificationStatus` → `RecoveryTransition`

**Persistence:** ChromaDB (local skill retrieval) + Convex (real-time dashboard events, skills, narration)

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | GPT-5.5 for planning, critic, curriculum |
| `MINECRAFT_HOST` | No | `localhost` | Minecraft server host |
| `MINECRAFT_PORT` | No | `25565` | Minecraft server port |
| `MINECRAFT_USERNAME` | No | `Voyager` | Bot username |
| `MINECRAFT_VERSION` | No | `1.20.4` | Minecraft protocol version |
| `CONVEX_URL` | No | — | Enables real-time Convex persistence |
| `ELEVENLABS_API_KEY` | No | — | Enables voice narration |
| `BRAIN_API_URL` | No | `http://localhost:8000` | Base URL for narration audio served by FastAPI |
| `CHROMA_DIR` | No | `brain/.chroma` | ChromaDB persistence directory |

## Dependencies

Install with:

```powershell
pip install -r brain\requirements.txt
```

Run the preflight checker to verify everything is ready:

```powershell
python scripts\preflight.py
```
