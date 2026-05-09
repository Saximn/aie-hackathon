/**
 * Optional prismarine-viewer wiring. Best-effort: if the plugin or WebGL
 * bindings fail (common on headless CI), we log and continue. The dashboard's
 * 2D top-down view does not depend on this.
 *
 * Also starts the HUD overlay server (see hud.ts) which serves a combined
 * page at http://localhost:HUD_PORT/ with the viewer in an iframe plus a
 * live health/food/inventory overlay.
 */

import type { Bot } from "mineflayer";
import { startHud } from "./hud.js";

const VIEWER_PORT = Number.parseInt(process.env.VIEWER_PORT ?? "3007", 10);
const VIEWER_FIRST_PERSON = (process.env.VIEWER_FIRST_PERSON ?? "true").toLowerCase() === "true";

export async function startViewer(bot: Bot): Promise<void> {
  try {
    const mod = await import("prismarine-viewer");
    const mineflayerViewer = (mod as unknown as { mineflayer: (bot: Bot, opts: object) => void }).mineflayer;
    if (typeof mineflayerViewer !== "function") {
      console.error("[viewer] prismarine-viewer.mineflayer not available; skipping");
    } else {
      mineflayerViewer(bot, { port: VIEWER_PORT, firstPerson: VIEWER_FIRST_PERSON });
      console.error(`[viewer] prismarine-viewer started on http://localhost:${VIEWER_PORT}`);
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`[viewer] failed to start prismarine-viewer: ${message}`);
  }

  // HUD overlay — best-effort, never throws across startViewer
  try {
    startHud(bot);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`[viewer] failed to start HUD server: ${message}`);
  }
}
