import { z } from "zod";
import type { PrimitiveAction, PrimitiveActionType, SupportedAction } from "./types.js";

export const SUPPORTED_ACTIONS: SupportedAction[] = [
  { type: "press_key", adapter: "generic_input", description: "Press and release a key.", requiredArgs: ["key"] },
  { type: "hold_key", adapter: "generic_input", description: "Hold a key for a duration.", requiredArgs: ["key", "durationMs"] },
  { type: "move_mouse", adapter: "generic_input", description: "Move the mouse by a relative delta.", requiredArgs: ["dx", "dy"] },
  { type: "click", adapter: "generic_input", description: "Click a mouse button.", requiredArgs: ["button"] },
  { type: "wait", adapter: "generic_input", description: "Wait for a duration.", requiredArgs: ["durationMs"] },
  { type: "open_menu", adapter: "generic_input", description: "Open a menu using a key.", requiredArgs: ["key"] },
  { type: "select_hotbar_slot", adapter: "generic_input", description: "Select a hotbar slot 1-9.", requiredArgs: ["slot"] },
  { type: "move_toward_visible_object", adapter: "generic_input", description: "Walk forward toward a visible object the brain has framed in the camera.", requiredArgs: ["object", "durationMs"] },
  { type: "interact_primary", adapter: "generic_input", description: "Use the primary interaction input (left mouse hold).", requiredArgs: ["durationMs"] },
  { type: "collect_block", adapter: "minecraft", description: "Mineflayer adapter: collect blocks of a given type.", requiredArgs: ["block", "count", "radius"] },
  { type: "craft_item", adapter: "minecraft", description: "Mineflayer adapter: craft an item.", requiredArgs: ["item", "count"] },
  { type: "build_shelter", adapter: "minecraft", description: "Mineflayer adapter: place blocks to form a shelter.", requiredArgs: ["material", "width", "depth", "height"] }
];

const KEY_PATTERN = /^[A-Za-z0-9]$|^(space|enter|escape|tab|shift|ctrl|alt|f[1-9]|f1[0-2])$/i;
const MOUSE_BUTTON = z.enum(["left", "right", "middle"]);

const ARG_SCHEMAS: Record<PrimitiveActionType, z.ZodTypeAny> = {
  press_key: z.object({ key: z.string().regex(KEY_PATTERN) }).strict(),
  hold_key: z.object({ key: z.string().regex(KEY_PATTERN), durationMs: z.number().int().min(1).max(15000) }).strict(),
  move_mouse: z.object({ dx: z.number().int().min(-2000).max(2000), dy: z.number().int().min(-2000).max(2000) }).strict(),
  click: z.object({ button: MOUSE_BUTTON }).strict(),
  wait: z.object({ durationMs: z.number().int().min(0).max(15000) }).strict(),
  open_menu: z.object({ key: z.string().regex(KEY_PATTERN) }).strict(),
  select_hotbar_slot: z.object({ slot: z.number().int().min(1).max(9) }).strict(),
  move_toward_visible_object: z.object({ object: z.string().min(1), durationMs: z.number().int().min(50).max(15000) }).strict(),
  interact_primary: z.object({ durationMs: z.number().int().min(1).max(15000) }).strict(),
  collect_block: z.object({ block: z.string().min(1), count: z.number().int().min(1).max(64), radius: z.number().int().min(1).max(64) }).strict(),
  craft_item: z.object({ item: z.string().min(1), count: z.number().int().min(1).max(64) }).strict(),
  build_shelter: z.object({ material: z.string().min(1), width: z.number().int().min(2).max(8), depth: z.number().int().min(2).max(8), height: z.number().int().min(2).max(4) }).strict()
};

export const PRIMITIVE_ACTION_SCHEMA = z.object({
  id: z.string().min(1),
  type: z.enum([
    "press_key", "hold_key", "move_mouse", "click", "wait", "open_menu",
    "select_hotbar_slot", "move_toward_visible_object", "interact_primary",
    "collect_block", "craft_item", "build_shelter"
  ]),
  args: z.record(z.string(), z.unknown()),
  expectedResult: z.record(z.string(), z.unknown()),
  timeoutMs: z.number().int().min(50).max(60000),
  adapter: z.enum(["generic_input", "minecraft"])
});

export interface ValidationResult {
  ok: boolean;
  reason?: string;
}

export function validateAction(action: PrimitiveAction): ValidationResult {
  const supported = SUPPORTED_ACTIONS.find(
    (s) => s.type === action.type && s.adapter === action.adapter
  );
  if (!supported) {
    return { ok: false, reason: `unsupported action type ${action.type} on adapter ${action.adapter}` };
  }
  const argSchema = ARG_SCHEMAS[action.type];
  const parsed = argSchema.safeParse(action.args);
  if (!parsed.success) {
    return { ok: false, reason: `invalid args: ${parsed.error.issues.map((e) => e.message).join("; ")}` };
  }
  return { ok: true };
}

export function isSupportedAction(action: PrimitiveAction): boolean {
  return validateAction(action).ok;
}
