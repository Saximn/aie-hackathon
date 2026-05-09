/**
 * OmniPlay-MC Mineflayer bridge entrypoint.
 *
 * Communicates with the Python brain via line-delimited JSON-RPC on stdin/stdout.
 * stderr is reserved for human-readable diagnostics.
 *
 * Usage:
 *   npm run bridge
 *   # or
 *   node --enable-source-maps dist/main.js
 */

import { startBridge } from "./voyagerBridge.js";

startBridge();
