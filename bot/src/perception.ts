import type { SymbolicObservation } from "./types.js";

/**
 * Reads optional symbolic state from the current game adapter.
 */
export async function readSymbolicState(): Promise<SymbolicObservation> {
  return {
    inventory: {},
    nearby_blocks: [],
    nearby_entities: [],
    raw_state: {}
  };
}

/**
 * Captures the current game window screenshot for VLM observation.
 */
export async function readScreenshot(): Promise<Buffer | null> {
  return null;
}
