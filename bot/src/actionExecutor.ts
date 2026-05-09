import type { ExecutionResult, PrimitiveAction } from "./types.js";

/**
 * Executes one grounded PrimitiveAction through the selected runtime adapter.
 */
export async function executeAction(action: PrimitiveAction): Promise<ExecutionResult> {
  // TODO(Person A): route generic_input actions to keyboard/mouse and
  // minecraft actions to the optional Mineflayer adapter.
  throw new Error(`TODO: execute action ${action.id}`);
}
