import { SUPPORTED_ACTIONS, isSupportedAction } from "./actionRegistry.js";
import { executeAction } from "./actionExecutor.js";
import { readScreenshot, readSymbolicState } from "./perception.js";
import type { ExecutionResult, PrimitiveAction, RuntimeActions, RuntimeHealth, RuntimeScreenshot, RuntimeState } from "./types.js";

/**
 * HTTP routes for the OmniForge runtime.
 *
 * TODO(Person A): implement:
 * - GET /health
 * - GET /state
 * - GET /screenshot
 * - GET /actions
 * - POST /action
 */
export function registerRoutes(): void {
  throw new Error("TODO: register runtime HTTP routes");
}

export function parseActionRequest(body: unknown): PrimitiveAction {
  if (!isPrimitiveAction(body)) {
    throw new Error("invalid Primitive Action request");
  }
  return body;
}

export function runtimeHealth(): RuntimeHealth {
  return {
    runtime: "ready",
    adapters: ["generic_input"],
    screenshot_available: false,
    symbolic_state_available: false,
    version: "0.1.0"
  };
}

export async function runtimeState(): Promise<RuntimeState> {
  return {
    available: false,
    symbolic: await readSymbolicState()
  };
}

export async function runtimeScreenshot(): Promise<RuntimeScreenshot> {
  const screenshot = await readScreenshot();
  return {
    screenshot_b64: screenshot?.toString("base64"),
    media_type: "image/png"
  };
}

export function runtimeActions(): RuntimeActions {
  return { actions: SUPPORTED_ACTIONS };
}

export async function runtimeAction(body: unknown): Promise<ExecutionResult> {
  const action = parseActionRequest(body);
  if (!isSupportedAction(action)) {
    return {
      action_id: action.id,
      success: false,
      result: "unsupported or malformed Primitive Action",
      evidence: {
        action_type: action.type,
        adapter: action.adapter
      }
    };
  }
  return await executeAction(action);
}

function isPrimitiveAction(value: unknown): value is PrimitiveAction {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Partial<PrimitiveAction>;
  return (
    typeof candidate.id === "string" &&
    typeof candidate.type === "string" &&
    typeof candidate.adapter === "string" &&
    typeof candidate.args === "object" &&
    candidate.args !== null &&
    typeof candidate.expected_result === "object" &&
    candidate.expected_result !== null &&
    typeof candidate.timeout_ms === "number"
  );
}
