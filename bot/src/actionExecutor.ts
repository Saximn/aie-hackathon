import type { ExecutionResult, PrimitiveAction } from "./types.js";

/**
 * Executes one grounded PrimitiveAction through Mineflayer.
 */
export async function executeAction(action: PrimitiveAction): Promise<ExecutionResult> {
  // TODO(Person A): route to Mineflayer movement, mining, crafting, combat, etc.
  return {
    actionId: action.id,
    success: false,
    result: "TODO: action execution not implemented"
  };
}
