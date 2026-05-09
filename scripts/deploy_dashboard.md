# Deploy the OmniPlay-MC dashboard to Vercel

Prereqs:
- Convex deployment URL (run `npx convex dev` once at the repo root and copy the printed URL).
- A Vercel account.

## One-time

```
npm i -g vercel
cd dashboard
vercel link
```

Follow the prompts; create a new project named `omniplay-mc-dashboard`.

## Configure environment

```
vercel env add NEXT_PUBLIC_CONVEX_URL  production
# paste your Convex prod URL when asked, e.g. https://gentle-toad-123.convex.cloud
vercel env add NEXT_PUBLIC_CONVEX_URL  preview
vercel env add NEXT_PUBLIC_CONVEX_URL  development
```

## Generate Convex API types before build

The dashboard imports `convex/_generated/api`. That file is produced by `npx convex dev` (or `npx convex deploy`) at the repo root. Run one of those before `vercel --prod` so codegen lands on disk and gets bundled.

## Deploy

```
cd dashboard
vercel --prod
```

You'll get a URL like `omniplay-mc-dashboard.vercel.app`. Open it; you should see:
- "OmniPlay-MC" header
- Empty panes if no agent has run yet (or panes populated from the latest episode if Convex has data).
- Live updates appear within ~500 ms once the agent runs again.

## Troubleshooting

- **Build error: cannot resolve `../../convex/_generated/api`** — run `npx convex deploy` in the repo root, then redeploy.
- **Empty data forever** — confirm `NEXT_PUBLIC_CONVEX_URL` is set on Vercel (not just locally).
- **CORS / WebSocket** — Convex handles this; no extra config needed.
