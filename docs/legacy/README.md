# docs/legacy

Code preserved from the previous **OmniForge** scaffold. Not in the OmniPlay-MC build path.

These files were moved during the Voyager-Plus refactor (Day 1.2 of the build plan) when the project pivoted from "typed-primitive HTTP server with VLM Observer" to "JSON-RPC JS-execution bridge for Voyager-style code-as-policy".

| Legacy file | Why archived |
| --- | --- |
| `bot/src/actionRegistry.ts` | Validated typed `PrimitiveAction` requests. Voyager generates JS code instead, so the registry is no longer the source of truth. |
| `bot/src/actionExecutor.ts` | Executed typed primitives via `@nut-tree-fork/nut-js` keyboard/mouse. Replaced by `bot/src/voyagerBridge.ts` running JS bodies inside the Mineflayer bot. |
| `bot/src/routes.ts` | Express HTTP routes. The bridge uses stdin/stdout JSON-RPC, no HTTP. |
| `bot/src/skills/*.ts` | Hand-coded TypeScript skills. Voyager-Plus stores skills as text+code in Chroma/Convex; nothing in the runtime is hand-coded per skill. |
| `bot/src/perception.ts` | Combined screenshot + symbolic state. The screenshot path is dropped (no VLM in this build); symbolic state lives in `bot/src/adapters/minecraft.ts::readSymbolicState`. |

If we ever revive a generic keyboard/mouse adapter or a typed-primitive contract, these are the starting point. Until then they should not be imported by the active build.
