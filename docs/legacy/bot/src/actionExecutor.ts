import { keyboard, mouse, Key, Button, Point, straightTo } from "@nut-tree-fork/nut-js";
import { validateAction } from "./actionRegistry.js";
import type { ExecutionResult, PrimitiveAction } from "./types.js";
import { getMinecraftAdapter, isMinecraftAdapterReady } from "./adapters/minecraft.js";

keyboard.config.autoDelayMs = 25;
mouse.config.autoDelayMs = 10;

const KEY_MAP: Record<string, Key> = {
  a: Key.A, b: Key.B, c: Key.C, d: Key.D, e: Key.E, f: Key.F,
  g: Key.G, h: Key.H, i: Key.I, j: Key.J, k: Key.K, l: Key.L,
  m: Key.M, n: Key.N, o: Key.O, p: Key.P, q: Key.Q, r: Key.R,
  s: Key.S, t: Key.T, u: Key.U, v: Key.V, w: Key.W, x: Key.X,
  y: Key.Y, z: Key.Z,
  "0": Key.Num0, "1": Key.Num1, "2": Key.Num2, "3": Key.Num3, "4": Key.Num4,
  "5": Key.Num5, "6": Key.Num6, "7": Key.Num7, "8": Key.Num8, "9": Key.Num9,
  space: Key.Space,
  enter: Key.Enter,
  escape: Key.Escape,
  tab: Key.Tab,
  shift: Key.LeftShift,
  ctrl: Key.LeftControl,
  alt: Key.LeftAlt,
  f1: Key.F1, f2: Key.F2, f3: Key.F3, f4: Key.F4, f5: Key.F5, f6: Key.F6,
  f7: Key.F7, f8: Key.F8, f9: Key.F9, f10: Key.F10, f11: Key.F11, f12: Key.F12
};

const BUTTON_MAP: Record<string, Button> = {
  left: Button.LEFT,
  right: Button.RIGHT,
  middle: Button.MIDDLE
};

function resolveKey(name: string): Key {
  const k = KEY_MAP[name.toLowerCase()];
  if (k === undefined) {
    throw new Error(`unmapped key: ${name}`);
  }
  return k;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function execGeneric(action: PrimitiveAction): Promise<ExecutionResult> {
  const args = action.args;
  switch (action.type) {
    case "press_key": {
      const key = resolveKey(args.key as string);
      await keyboard.pressKey(key);
      await keyboard.releaseKey(key);
      return ok(action, `pressed ${args.key}`);
    }
    case "hold_key": {
      const key = resolveKey(args.key as string);
      const duration = args.durationMs as number;
      await keyboard.pressKey(key);
      await sleep(duration);
      await keyboard.releaseKey(key);
      return ok(action, `held ${args.key} for ${duration}ms`);
    }
    case "move_mouse": {
      const dx = args.dx as number;
      const dy = args.dy as number;
      const cur = await mouse.getPosition();
      await mouse.move(straightTo(new Point(cur.x + dx, cur.y + dy)));
      return ok(action, `moved mouse by (${dx},${dy})`, { from: { x: cur.x, y: cur.y } });
    }
    case "click": {
      const button = BUTTON_MAP[(args.button as string).toLowerCase()];
      await mouse.click(button);
      return ok(action, `clicked ${args.button}`);
    }
    case "wait": {
      await sleep(args.durationMs as number);
      return ok(action, `waited ${args.durationMs}ms`);
    }
    case "open_menu": {
      const key = resolveKey(args.key as string);
      await keyboard.pressKey(key);
      await keyboard.releaseKey(key);
      await sleep(150);
      return ok(action, `opened menu via ${args.key}`);
    }
    case "select_hotbar_slot": {
      const slot = args.slot as number;
      const key = resolveKey(String(slot));
      await keyboard.pressKey(key);
      await keyboard.releaseKey(key);
      return ok(action, `selected hotbar slot ${slot}`);
    }
    case "move_toward_visible_object": {
      const duration = args.durationMs as number;
      await keyboard.pressKey(Key.W);
      await sleep(duration);
      await keyboard.releaseKey(Key.W);
      return ok(action, `walked toward ${args.object} for ${duration}ms`);
    }
    case "interact_primary": {
      const duration = args.durationMs as number;
      await mouse.pressButton(Button.LEFT);
      await sleep(duration);
      await mouse.releaseButton(Button.LEFT);
      return ok(action, `held primary interact for ${duration}ms`);
    }
    default:
      throw new Error(`generic adapter does not support ${action.type}`);
  }
}

async function execMinecraft(action: PrimitiveAction): Promise<ExecutionResult> {
  if (!isMinecraftAdapterReady()) {
    return fail(action, "minecraft adapter not connected");
  }
  const adapter = getMinecraftAdapter();
  switch (action.type) {
    case "collect_block": {
      const evidence = await adapter.collectBlock(
        action.args.block as string,
        action.args.count as number,
        action.args.radius as number,
        action.timeoutMs
      );
      return ok(action, `collected ${action.args.block}`, evidence);
    }
    case "craft_item": {
      const evidence = await adapter.craftItem(
        action.args.item as string,
        action.args.count as number,
        action.timeoutMs
      );
      return ok(action, `crafted ${action.args.item}`, evidence);
    }
    case "build_shelter": {
      const evidence = await adapter.buildShelter(
        action.args.material as string,
        action.args.width as number,
        action.args.depth as number,
        action.args.height as number,
        action.timeoutMs
      );
      return ok(action, `built shelter`, evidence);
    }
    default:
      throw new Error(`minecraft adapter does not support ${action.type}`);
  }
}

function ok(action: PrimitiveAction, result: string, evidence: Record<string, unknown> = {}): ExecutionResult {
  return { actionId: action.id, success: true, result, evidence };
}

function fail(action: PrimitiveAction, result: string, evidence: Record<string, unknown> = {}): ExecutionResult {
  return { actionId: action.id, success: false, result, evidence };
}

export async function executeAction(action: PrimitiveAction): Promise<ExecutionResult> {
  const validation = validateAction(action);
  if (!validation.ok) {
    return fail(action, `validation: ${validation.reason}`);
  }

  const deadline = Date.now() + action.timeoutMs;
  try {
    const result =
      action.adapter === "minecraft"
        ? await execMinecraft(action)
        : await execGeneric(action);
    if (Date.now() > deadline) {
      result.evidence = { ...result.evidence, exceededTimeoutMs: Date.now() - (deadline - action.timeoutMs) };
    }
    return result;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return fail(action, message);
  }
}
