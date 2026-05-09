import type { ExecutionResult } from "../types.js";

/**
 * Seeded runtime skill: gather wood through Mineflayer primitives.
 */
export async function gatherWood(count: number): Promise<ExecutionResult> {
  // TODO(Person A): implement using pathfinding and block mining.
  return { success: false, result: `TODO: gather ${count} wood` };
}
