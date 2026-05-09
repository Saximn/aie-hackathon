/**
 * Line-delimited JSON-RPC bridge over stdin/stdout for the OmniPlay-MC brain.
 *
 * Methods:
 *   - connect({ host, port, username, version }) -> { ok, version, username }
 *   - runJs({ code, timeoutMs }) -> RunJsResult
 *   - getState() -> SymbolicObservation
 *   - chat({ message }) -> { ok }
 *   - disconnect() -> { ok }
 *   - ping() -> { pong: true }
 *
 * Generated JS bodies receive (bot, mcData, Vec3, goals, Movements) and run
 * inside an async IIFE wrapper. Errors are captured and returned in the
 * response payload, never thrown across the bridge.
 */

import readline from "node:readline";
import { setTimeout as wait } from "node:timers/promises";
import type { Bot } from "mineflayer";
import { getMinecraftAdapter, isMinecraftAdapterReady, tryConnectMinecraft } from "./adapters/minecraft.js";
import { buildSandbox, loadSkillPlugins } from "./skillPrimitives.js";
import { startViewer } from "./viewer.js";
import type {
  BridgeRequest,
  BridgeResponse,
  ConnectParams,
  RunJsParams,
  RunJsResult,
  SymbolicObservation
} from "./types.js";

const DEFAULT_TIMEOUT_MS = 60_000;
const MAX_TIMEOUT_MS = 300_000;

// stdout is reserved for the JSON-RPC channel. Redirect any incidental
// console.log / console.info / console.warn from Mineflayer or generated JS
// to stderr so the protocol stays clean.
const originalConsoleError = console.error.bind(console);
console.log = (...args: unknown[]) => originalConsoleError("[bridge:log]", ...args);
console.info = (...args: unknown[]) => originalConsoleError("[bridge:info]", ...args);
console.warn = (...args: unknown[]) => originalConsoleError("[bridge:warn]", ...args);

let pluginsLoaded = false;
let viewerStarted = false;

function writeResponse(res: BridgeResponse): void {
  process.stdout.write(`${JSON.stringify(res)}\n`);
}

function logErr(...args: unknown[]): void {
  const text = args.map((a) => (typeof a === "string" ? a : JSON.stringify(a))).join(" ");
  process.stderr.write(`[bridge] ${text}\n`);
}

async function handleConnect(params: ConnectParams): Promise<{ ok: boolean; version: string; username: string }> {
  const ok = await tryConnectMinecraft({
    host: params.host,
    port: params.port,
    username: params.username,
    version: params.version
  });
  if (!ok) {
    const status = getMinecraftAdapter().status();
    throw new Error(`mineflayer connect failed: ${status.lastError ?? "unknown"}`);
  }
  const bot = getBot();
  if (!pluginsLoaded) {
    loadSkillPlugins(bot);
    pluginsLoaded = true;
  }
  if (!viewerStarted) {
    await startViewer(bot);
    viewerStarted = true;
  }
  return { ok: true, version: bot.version, username: bot.username };
}

function getBot(): Bot {
  const adapter = getMinecraftAdapter();
  const bot = (adapter as unknown as { bot: Bot | null }).bot;
  if (!bot || !isMinecraftAdapterReady()) {
    throw new Error("mineflayer not connected; call connect first");
  }
  return bot;
}

async function safeReadState(): Promise<SymbolicObservation | undefined> {
  try {
    if (!isMinecraftAdapterReady()) return undefined;
    return await getMinecraftAdapter().readSymbolicState();
  } catch (err) {
    logErr("readSymbolicState failed:", err instanceof Error ? err.message : String(err));
    return undefined;
  }
}

async function handleRunJs(params: RunJsParams): Promise<RunJsResult> {
  const bot = getBot();
  const code = params.code;
  if (typeof code !== "string" || code.trim().length === 0) {
    return { ok: false, error: { message: "runJs: empty code" }, durationMs: 0 };
  }
  const timeoutMs = Math.min(MAX_TIMEOUT_MS, Math.max(1_000, params.timeoutMs ?? DEFAULT_TIMEOUT_MS));
  const sandbox = buildSandbox(bot);
  const startedAt = Date.now();

  const wrapped = `return (async (bot, mcData, Vec3, goals, Movements) => {\n${code}\n})(bot, mcData, Vec3, goals, Movements);`;

  let cancelled = false;
  const work = (async (): Promise<unknown> => {
    const factory = new Function("bot", "mcData", "Vec3", "goals", "Movements", wrapped) as (
      ...a: unknown[]
    ) => Promise<unknown>;
    return factory(sandbox.bot, sandbox.mcData, sandbox.Vec3, sandbox.goals, sandbox.Movements);
  })();

  const guard = (async (): Promise<{ timedOut: true }> => {
    await wait(timeoutMs);
    cancelled = true;
    return { timedOut: true };
  })();

  try {
    const winner = await Promise.race([work, guard]);
    const durationMs = Date.now() - startedAt;
    if (cancelled || (typeof winner === "object" && winner !== null && (winner as { timedOut?: boolean }).timedOut)) {
      const stateAfter = await safeReadState();
      try {
        bot.pathfinder?.stop?.();
      } catch {
        /* ignore */
      }
      return { ok: false, error: { message: `runJs timeout after ${timeoutMs}ms` }, durationMs, stateAfter };
    }
    const stateAfter = await safeReadState();
    return { ok: true, result: serialize(winner), durationMs, stateAfter };
  } catch (err) {
    const durationMs = Date.now() - startedAt;
    const stateAfter = await safeReadState();
    const message = err instanceof Error ? err.message : String(err);
    const stack = err instanceof Error ? err.stack : undefined;
    return { ok: false, error: { message, stack }, durationMs, stateAfter };
  }
}

function serialize(value: unknown, depth = 0): unknown {
  if (depth > 4) return "[truncated]";
  if (value === null || value === undefined) return value;
  const t = typeof value;
  if (t === "string" || t === "number" || t === "boolean") return value;
  if (Array.isArray(value)) return value.slice(0, 50).map((v) => serialize(v, depth + 1));
  if (t === "object") {
    const out: Record<string, unknown> = {};
    let count = 0;
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      if (count >= 50) {
        out["..."] = "truncated";
        break;
      }
      try {
        out[k] = serialize(v, depth + 1);
      } catch {
        out[k] = "[unserializable]";
      }
      count += 1;
    }
    return out;
  }
  return String(value);
}

async function handleChat(params: { message: string }): Promise<{ ok: boolean }> {
  const bot = getBot();
  bot.chat(params.message);
  return { ok: true };
}

async function handleDispatch(req: BridgeRequest): Promise<BridgeResponse> {
  try {
    switch (req.method) {
      case "ping":
        return { id: req.id, ok: true, result: { pong: true } };
      case "connect": {
        const params = (req.params ?? {}) as unknown as ConnectParams;
        return { id: req.id, ok: true, result: await handleConnect(params) };
      }
      case "runJs": {
        const params = (req.params ?? {}) as unknown as RunJsParams;
        return { id: req.id, ok: true, result: await handleRunJs(params) };
      }
      case "getState": {
        const bot = getBot();
        const state = await getMinecraftAdapter().readSymbolicState();
        return { id: req.id, ok: true, result: { state, version: bot.version, username: bot.username } };
      }
      case "chat": {
        const params = (req.params ?? {}) as unknown as { message: string };
        return { id: req.id, ok: true, result: await handleChat(params) };
      }
      case "disconnect": {
        getMinecraftAdapter().disconnect();
        return { id: req.id, ok: true, result: { ok: true } };
      }
      default:
        return { id: req.id, ok: false, error: { message: `unknown method ${req.method}` } };
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const stack = err instanceof Error ? err.stack : undefined;
    return { id: req.id, ok: false, error: { message, stack } };
  }
}

export function startBridge(): void {
  process.stdout.setDefaultEncoding?.("utf8");
  const rl = readline.createInterface({ input: process.stdin, terminal: false });
  rl.on("line", (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    let req: BridgeRequest;
    try {
      req = JSON.parse(trimmed) as BridgeRequest;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      writeResponse({ id: "parse-error", ok: false, error: { message: `bad json: ${message}` } });
      return;
    }
    void handleDispatch(req).then(writeResponse).catch((err: unknown) => {
      const message = err instanceof Error ? err.message : String(err);
      writeResponse({ id: req.id, ok: false, error: { message } });
    });
  });
  rl.on("close", () => {
    logErr("stdin closed; exiting");
    try {
      getMinecraftAdapter().disconnect();
    } catch {
      /* ignore */
    }
    process.exit(0);
  });
  logErr("bridge ready");
}
