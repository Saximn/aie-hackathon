import type { PrimitiveAction, SupportedAction } from "./types.js";

export const SUPPORTED_ACTIONS: SupportedAction[] = [
  { type: "press_key", adapter: "generic_input", description: "Press and release a key.", required_args: ["key"] },
  { type: "hold_key", adapter: "generic_input", description: "Hold a key for a duration.", required_args: ["key", "duration_ms"] },
  { type: "move_mouse", adapter: "generic_input", description: "Move the mouse by a relative delta.", required_args: ["dx", "dy"] },
  { type: "click", adapter: "generic_input", description: "Click a mouse button.", required_args: ["button"] },
  { type: "wait", adapter: "generic_input", description: "Wait for a duration.", required_args: ["duration_ms"] },
  { type: "open_menu", adapter: "generic_input", description: "Open a menu using a key.", required_args: ["key"] },
  { type: "select_hotbar_slot", adapter: "generic_input", description: "Select a hotbar slot.", required_args: ["slot"] },
  { type: "move_toward_visible_object", adapter: "generic_input", description: "Move toward a visible object.", required_args: ["object", "duration_ms"] },
  { type: "interact_primary", adapter: "generic_input", description: "Use the primary interaction input.", required_args: [] },
  { type: "collect_block", adapter: "minecraft", description: "Optional Minecraft adapter block collection.", required_args: ["block", "count", "radius"] },
  { type: "craft_item", adapter: "minecraft", description: "Optional Minecraft adapter crafting.", required_args: ["item", "count"] },
  { type: "build_shelter", adapter: "minecraft", description: "Optional Minecraft adapter shelter build.", required_args: ["material", "width", "depth", "height"] }
];

export function isSupportedAction(action: PrimitiveAction): boolean {
  const metadata = SUPPORTED_ACTIONS.find((candidate) => candidate.type === action.type && candidate.adapter === action.adapter);
  if (!metadata) {
    return false;
  }

  return metadata.required_args.every((name) => action.args[name] !== undefined && action.args[name] !== null && action.args[name] !== "");
}
