# OmniPlay-MC Demo Runbook

> **TL;DR — two commands, then hit record.**
> `python scripts\preflight.py` → `scripts\start_all.ps1`

---

## Pre-flight (60 seconds)

```powershell
# 1. Activate venv and run the checker
. .venv\Scripts\Activate.ps1
python scripts\preflight.py
```

All checks must show `[OK]` or `[WARN]` (no `[FAIL]`).

```powershell
# 2. One-click launch (MC server → Convex dev → Dashboard → Brain shell)
scripts\start_all.ps1
```

`start_all.ps1` runs `preflight.py` again and aborts if anything is broken.
Wait until the 'MC server' window shows **"Done! For help, type "help""** before continuing.

---

## Take (recording path)

1. **Hit record** in OBS (layout: dashboard left half, Minecraft client right half).

2. **Voice-over intro (5 s)**:
   *"OmniPlay-MC. Voyager modernized onto GPT-5.5, with live observability."*

3. **Start the agent** — switch to the **Brain shell** window and run:
   ```
   python brain\run_agent.py --demo --log-level INFO
   ```

4. **Show the dashboard** in order (10–15 s each panel):
   | Panel | What to point at |
   |---|---|
   | **GoalPanel** | First `goal_received` event |
   | **BotView** | Bot position updating in real time |
   | **EventFeed** | `plan_created` → `action_completed` → `verification_completed` |
   | **SkillLibrary** | Counter ticks up when the first task succeeds |
   | **NarrationPlayer** | Voice plays the narration clip |

5. **Voice-over outro (5 s)**:
   *"Cross-session skill memory in Convex. Public Vercel URL. Cash-prize stack: GPT-5.5 + Convex + ElevenLabs."*

6. **Stop record.**

### Cuts to make if a take runs long

- Skip the seed step in voice-over.
- Cut to the dashboard the moment the first `verification_completed` fires.
- Hard cut to the Vercel public URL with one skill in the library.

---

## Live demo path

Recovery steps for the five most likely on-stage failures — each under 10 s.

| Symptom | Recovery |
|---|---|
| **Bot disconnected** | In the MC server window: `/say bot reconnecting`<br>In Brain shell: `python brain\run_agent.py --task "chop a tree"` |
| **Dashboard stale / blank** | Hard-refresh the browser (Ctrl+Shift+R). If Convex shows nothing, check the 'Convex dev' window for auth errors. |
| **Narration silent** | Confirm `ELEVENLABS_API_KEY` in `brain/.env`. If missing, mention it's optional and continue pointing to the EventFeed scroll. |
| **MC server crash** | Run `scripts\start_server.bat` in a fresh window; the bot reconnects on the next agent cycle. |
| **`/spectate Voyager` failed** | Run `/op <your-username>` in the server console, then retry in the Minecraft client. |

---

## After the demo

```
Ctrl+C   # in the Brain shell window
```

Confirm:

- `brain/.chroma/` has skill rows.
- Convex dashboard shows ≥ 1 row in `skills`.
- Stop the MC server: type `stop` in the 'MC server' window.

---

<details>
<summary>Manual fallback (if start_all.ps1 fails)</summary>

Run each command in a separate terminal window:

1. **MC server**
   ```
   scripts\start_server.bat
   ```
   Wait ~25 s for "Done!" in the log.

2. **Convex dev** (only if `CONVEX_URL` is set)
   ```
   npx convex dev
   ```

3. **Dashboard**
   ```
   cd dashboard
   npm run dev
   ```
   Open http://localhost:3000.

4. **Seed skills** (optional, improves cycle-1 retrieval)
   ```
   . .venv\Scripts\Activate.ps1
   python scripts\seed_skills.py
   ```

5. **Open Minecraft client** → Multiplayer → connect to `localhost`.
   In the server console: `/op <your-username>`
   In the MC client: `/gamemode spectator`

6. **OBS**: capture dashboard (left half) + Minecraft client (right half).

7. **Brain**
   ```
   . .venv\Scripts\Activate.ps1
   python brain\run_agent.py --demo --log-level INFO
   ```

</details>
