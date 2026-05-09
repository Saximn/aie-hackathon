import type { ExecutionResult, PrimitiveAction } from "./types.js";

/**
 * Executes one grounded PrimitiveAction through the selected runtime adapter.
 */
export async function executeAction(action: PrimitiveAction): Promise<ExecutionResult> {
  return {
    action_id: action.id,
    success: false,
    result: "runtime adapter is not configured",
    evidence: {
      action_type: action.type,
      adapter: action.adapter
    }
  };
}
