# OmniPlay-MC Demo Runbook (90 seconds, 2 takes max)

## Pre-flight (run once, ~30 minutes before)

1. `scripts\start_server.bat` — Fabric server up on :25565.
2. `npx convex dev` (repo root) — Convex backend running, schema deployed.
3. `cd dashboard && npm run dev` — local dashboard on http://localhost:3000.
4. Open Minecraft client → Multiplayer → connect to `localhost`.
5. In MC, run `/op <your-username>` from the server console once, then in the client `/gamemode spectator`.
6. (Optional) `python scripts\seed_skills.py` — pre-seeds Chroma + Convex with 5 baseline skills so the agent retrieves something on cycle 1.
7. Set OBS Studio to capture: dashboard window (left half) + Minecraft client (right half).

## Take

1. Hit record.
2. Voice-over intro (5s): *"OmniPlay-MC. Voyager modernized onto GPT-5.5, with live observability."*
3. Run the demo command:
   ```
   .venv\Scripts\activate
   python brain\run_agent.py --demo --log-level INFO
   ```
4. Show on the dashboard, in order (10–15 s each):
   - **GoalPanel** receives the first `goal_received` event.
   - **BotView** updates in real time as the bot moves.
   - **EventFeed** scrolls — point out `plan_created` → `action_completed` → `verification_completed`.
   - **SkillLibrary** ticks up by one when the first task succeeds.
   - **NarrationPlayer** speaks the narration.
5. Voice-over outro (5s): *"Cross-session skill memory in Convex. Public Vercel URL. Cash-prize stack: GPT-5.5 + Convex + ElevenLabs."*
6. Stop record.

## Cuts to make if a take goes long

- Skip the seed step in voice-over.
- Cut to the dashboard the moment the first `verification_completed` fires.
- Hard cut to the Vercel public URL with one skill in the library at the end.

## After

`Ctrl+C` the brain process. Confirm:

- `brain/.chroma/` has skill rows.
- Convex dashboard shows ≥1 row in `skills`.
- Stop the server with `stop` in the server console.
