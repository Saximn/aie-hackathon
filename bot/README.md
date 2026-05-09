# OmniPlay-MC Bridge

Mineflayer bridge for the OmniPlay-MC (Voyager-Plus) brain.

The brain spawns this process and talks to it over **line-delimited JSON-RPC on stdin/stdout**. stderr is reserved for human-readable diagnostics.

## Methods

- `connect({ host, port, username, version })` — connect Mineflayer to the Fabric server.
- `runJs({ code, timeoutMs })` — eval an async JS body with `(bot, mcData, Vec3, goals, Movements)` in scope and return `{ ok, result, error, durationMs, stateAfter }`.
- `getState()` — return current `SymbolicObservation` plus version + username.
- `chat({ message })` — `bot.chat`.
- `disconnect()` — quit the Mineflayer client.
- `ping()` — health check.

Generated JS bodies have `mineflayer-pathfinder`, `mineflayer-collectblock`, and `mineflayer-tool` plugins loaded. They run inside an async IIFE; throws and timeouts are captured and returned as structured errors, never propagated across the bridge.

## Run

```
npm install
npm run bridge
```

Optional: `VIEWER_PORT=3007 VIEWER_FIRST_PERSON=true` controls the local prismarine-viewer (best-effort; ignored if it fails to load).

## Layout

- `src/main.ts` — entrypoint.
- `src/voyagerBridge.ts` — JSON-RPC dispatcher and `runJs` sandbox.
- `src/skillPrimitives.ts` — plugin loading and the sandbox object handed to generated JS.
- `src/viewer.ts` — optional prismarine-viewer wiring.
- `src/adapters/minecraft.ts` — Mineflayer connect + symbolic state read.
- `src/types.ts` — shared TypeScript contracts.

The previous typed-primitive HTTP server (`actionRegistry`, `actionExecutor`, `routes`, hand-coded `skills/*`, generic-input `perception`) is preserved under `docs/legacy/bot/` and is not part of this build.
