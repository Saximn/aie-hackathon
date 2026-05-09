import type { WorldState } from "./types.js";

/**
 * Converts Mineflayer bot state into the shared WorldState contract.
 */
export async function readWorldState(): Promise<WorldState> {
  // TODO(Person A): read position, inventory, time, blocks, entities, and biome.
  throw new Error("TODO: read world state from Mineflayer");
}

export async function readScreenshot(): Promise<Buffer> {
  // TODO(Person A): capture a first-person screenshot for optional VLM input.
  throw new Error("TODO: capture screenshot");
}
