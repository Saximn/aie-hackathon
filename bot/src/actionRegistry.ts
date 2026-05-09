import type { PrimitiveAction, SupportedAction } from "./types.js";

export const SUPPORTED_ACTIONS: SupportedAction[] = [
  { type: "move_to", description: "Move to a coordinate.", requiredArgs: ["x", "y", "z"] },
  { type: "mine_block", description: "Mine nearby blocks of a type.", requiredArgs: ["blockType"] },
  { type: "craft", description: "Craft an item.", requiredArgs: ["itemName", "count"] },
  { type: "equip", description: "Equip an inventory item.", requiredArgs: ["itemName"] },
  { type: "eat", description: "Eat food from inventory.", requiredArgs: ["foodName"] },
  { type: "attack_nearest", description: "Attack nearest mob of a type.", requiredArgs: ["mobType"] },
  { type: "sleep", description: "Sleep in an available bed.", requiredArgs: [] },
  { type: "place_block", description: "Place a block at a coordinate.", requiredArgs: ["blockName", "x", "y", "z"] },
  { type: "chat", description: "Send a chat message.", requiredArgs: ["message"] },
  { type: "explore", description: "Explore a cardinal direction.", requiredArgs: ["direction"] },
  { type: "look_around", description: "Scan surroundings.", requiredArgs: [] },
  { type: "call_skill", description: "Run a seeded runtime skill.", requiredArgs: ["skillName"] }
];

export function isSupportedAction(action: PrimitiveAction): boolean {
  // TODO(Person A): validate args and supported seeded skill names.
  return SUPPORTED_ACTIONS.some((candidate) => candidate.type === action.type);
}
