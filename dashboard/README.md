# OmniPlay-MC Dashboard

Next.js 14 (App Router) dashboard for the live agent. Reads from Convex and re-renders in real time as the AgentLoop emits events.

## Layout

- **Bot view** — 2D top-down render driven by `current_state.symbolic` (position + nearby blocks). Health and hunger overlaid.
- **Goal panel** — latest task, the planner's explanation, the JS body the action agent emitted, and the critic verdict.
- **Event feed** — live scroll of every Agent Event (goal, plan, action, verification, skill).
- **Skill library** — every learned skill, expandable to its full code.
- **Narration footer** — autoplays the latest ElevenLabs clip, with a mute toggle.

## Run

```
npm install
cp .env.example .env.local       # set NEXT_PUBLIC_CONVEX_URL
npm run dev
```

## Deploy

```
vercel link                       # one-time
vercel env add NEXT_PUBLIC_CONVEX_URL
vercel --prod
```

## Note on `lib/convex_api.ts`

This file re-exports `convex/_generated/api`. That generated module only exists after `npx convex dev` has run at the repo root. Run convex dev once before `npm run build` here.
