import type { PrimitiveAction } from "./types.js";

/**
 * HTTP routes for the Mineflayer Runtime.
 * TODO(Person A): implement GET /health, /state, /screenshot, /actions and
 * POST /action using the selected Node HTTP framework.
 */
export function registerRoutes(): void {
  throw new Error("TODO: register bot HTTP routes");
}

export function parseActionRequest(body: unknown): PrimitiveAction {
  // TODO(Person A): validate request body before execution.
  return body as PrimitiveAction;
}
