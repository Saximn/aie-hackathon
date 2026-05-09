/**
 * Re-exports the Mineflayer plugin surface that GPT-5.5-generated code is
 * allowed to use. Importing this module loads the plugins onto a bot instance.
 */

import type { Bot } from "mineflayer";
import pathfinderModule from "mineflayer-pathfinder";
import collectBlockModule from "mineflayer-collectblock";
import toolModule from "mineflayer-tool";
import vec3Module from "vec3";
import minecraftData from "minecraft-data";

const { pathfinder, Movements, goals } = pathfinderModule as unknown as {
  pathfinder: Parameters<Bot["loadPlugin"]>[0];
  Movements: new (bot: Bot) => unknown;
  goals: Record<string, unknown>;
};

const Vec3 = (vec3Module as unknown as { Vec3?: unknown }).Vec3 ?? (vec3Module as unknown);

const collectPlugin = (collectBlockModule as unknown as { plugin?: unknown }).plugin ?? collectBlockModule;
const toolPluginFn = (toolModule as unknown as { plugin?: unknown }).plugin ?? toolModule;

export { pathfinder, Movements, goals, Vec3, minecraftData };

export function loadSkillPlugins(bot: Bot): void {
  bot.loadPlugin(pathfinder);
  bot.loadPlugin(collectPlugin as Parameters<Bot["loadPlugin"]>[0]);
  bot.loadPlugin(toolPluginFn as Parameters<Bot["loadPlugin"]>[0]);
}

export interface Sandbox {
  bot: Bot;
  mcData: ReturnType<typeof minecraftData>;
  Vec3: unknown;
  goals: Record<string, unknown>;
  Movements: new (bot: Bot) => unknown;
}

/**
 * Build the sandbox handed to generated JS bodies. The action agent calls
 * its code as `(async (bot, mcData, Vec3, goals, Movements) => { ... body ... })(...)`.
 */
export function buildSandbox(bot: Bot): Sandbox {
  return {
    bot,
    mcData: minecraftData(bot.version),
    Vec3,
    goals,
    Movements
  };
}
