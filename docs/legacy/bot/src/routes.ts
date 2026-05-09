import type { PrimitiveAction } from "./types.js";

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
  // TODO(Person A): validate request body before execution.
  return body as PrimitiveAction;
}
