import type { PrimitiveAction, SupportedAction } from "./types.js";

export const SUPPORTED_ACTIONS: SupportedAction[] = [
  { type: "press_key", adapter: "generic_input", description: "Press and release a key.", requiredArgs: ["key"] },
  { type: "hold_key", adapter: "generic_input", description: "Hold a key for a duration.", requiredArgs: ["key", "durationMs"] },
  { type: "move_mouse", adapter: "generic_input", description: "Move the mouse by a relative delta.", requiredArgs: ["dx", "dy"] },
  { type: "click", adapter: "generic_input", description: "Click a mouse button.", requiredArgs: ["button"] },
  { type: "wait", adapter: "generic_input", description: "Wait for a duration.", requiredArgs: ["durationMs"] },
  { type: "open_menu", adapter: "generic_input", description: "Open a menu using a key.", requiredArgs: ["key"] },
  { type: "select_hotbar_slot", adapter: "generic_input", description: "Select a hotbar slot.", requiredArgs: ["slot"] },
  { type: "move_toward_visible_object", adapter: "generic_input", description: "Move toward a visible object.", requiredArgs: ["object", "durationMs"] },
  { type: "interact_primary", adapter: "generic_input", description: "Use the primary interaction input.", requiredArgs: ["durationMs"] },
  { type: "collect_block", adapter: "minecraft", description: "Optional Minecraft adapter block collection.", requiredArgs: ["block", "count", "radius"] },
  { type: "craft_item", adapter: "minecraft", description: "Optional Minecraft adapter crafting.", requiredArgs: ["item", "count"] },
  { type: "build_shelter", adapter: "minecraft", description: "Optional Minecraft adapter shelter build.", requiredArgs: ["material", "width", "depth", "height"] }
];

export function isSupportedAction(action: PrimitiveAction): boolean {
  // TODO(Person A): validate args, adapter availability, and runtime safety.
  return SUPPORTED_ACTIONS.some((candidate) => candidate.type === action.type && candidate.adapter === action.adapter);
}
