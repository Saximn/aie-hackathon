import type { SymbolicObservation } from "./types.js";

/**
 * Reads optional symbolic state from the current game adapter.
 */
export async function readSymbolicState(): Promise<SymbolicObservation> {
  // TODO(Person A): read position, inventory, health, nearby blocks, entities, and biome when available.
  throw new Error("TODO: read symbolic state");
}

/**
 * Captures the current game window screenshot for VLM observation.
 */
export async function readScreenshot(): Promise<Buffer> {
  // TODO(Person A): capture a first-person screenshot from the game window.
  throw new Error("TODO: capture screenshot");
}
