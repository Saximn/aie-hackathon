/**
 * Lightweight HUD HTTP server.
 *
 * Starts a Node http server on HUD_PORT (default 3008) that exposes:
 *   GET /        → HTML page: viewer iframe (port 3007) + real-time HUD overlay
 *   GET /hud     → alias for /
 *   GET /state   → JSON snapshot of health / food / xp / inventory
 *
 * The overlay polls /state every 1.5 s using vanilla JS — no React, no build step.
 * State is updated eagerly on mineflayer health/inventory events and also every 2 s
 * via a setInterval fallback.
 */

import http from "node:http";
import type { Bot } from "mineflayer";

const HUD_PORT = Number.parseInt(process.env.HUD_PORT ?? "3008", 10);
const VIEWER_PORT = Number.parseInt(process.env.VIEWER_PORT ?? "3007", 10);

interface InventoryItem {
  name: string;
  count: number;
  slot: number;
}

interface HudState {
  health: number;
  food: number;
  xp: number;
  inventory: InventoryItem[];
  connected: boolean;
}

let cachedState: HudState = {
  health: 0,
  food: 0,
  xp: 0,
  inventory: [],
  connected: false,
};

function captureState(bot: Bot): void {
  try {
    const inventory: InventoryItem[] = bot.inventory.items().map((item) => ({
      name: item.name,
      count: item.count,
      slot: item.slot,
    }));
    cachedState = {
      health: bot.health ?? 0,
      food: bot.food ?? 0,
      xp: bot.experience?.level ?? 0,
      inventory,
      connected: true,
    };
  } catch {
    // ignore — bot may not be fully initialised yet
  }
}

function htmlPage(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OmniPlay MC — Live View</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #000; overflow: hidden; font-family: 'Courier New', monospace; }

    #viewer-frame { width: 100vw; height: 100vh; border: none; display: block; }

    /* HUD anchored to bottom-centre */
    #hud {
      position: fixed; bottom: 0; left: 0; right: 0;
      pointer-events: none; z-index: 100;
      display: flex; flex-direction: column; align-items: center;
      padding-bottom: 14px; gap: 6px;
    }

    /* Stat pills */
    .stat-row { display: flex; gap: 12px; }
    .stat {
      background: rgba(0, 0, 0, 0.78);
      border: 1px solid rgba(255, 255, 255, 0.18);
      padding: 4px 14px; border-radius: 2px;
      color: #fff; font-size: 14px; letter-spacing: 0.4px;
      text-shadow: 1px 1px 0 #000;
    }
    #hud-health { color: #ff5555; }
    #hud-food   { color: #ffaa44; }
    #hud-xp     { color: #55ff55; }

    /* Inventory hotbar */
    #inv-bar {
      display: flex; flex-wrap: wrap; gap: 3px;
      justify-content: center;
      background: rgba(0, 0, 0, 0.82);
      border: 2px solid rgba(180, 180, 180, 0.35);
      padding: 5px 7px; border-radius: 2px;
      max-width: 92vw;
    }
    .slot {
      width: 42px; height: 42px;
      border: 1px solid rgba(90, 90, 90, 0.8);
      background: rgba(55, 55, 55, 0.95);
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      position: relative; overflow: hidden;
      border-radius: 1px;
    }
    .slot .sname {
      font-size: 7px; color: #ccc; text-align: center;
      line-height: 1.2; padding: 0 2px; word-break: break-all;
    }
    .slot .scnt {
      position: absolute; bottom: 1px; right: 2px;
      font-size: 11px; font-weight: bold;
      color: #ffff55; text-shadow: 1px 1px 0 #000;
    }

    /* Connection status indicator */
    #conn-dot {
      position: fixed; top: 10px; right: 12px;
      width: 10px; height: 10px; border-radius: 50%;
      background: #555; transition: background 0.3s;
      z-index: 200;
    }
    #conn-dot.ok  { background: #55ff55; }
    #conn-dot.err { background: #ff3333; }
  </style>
</head>
<body>
  <iframe id="viewer-frame" src="http://localhost:${VIEWER_PORT}"></iframe>

  <div id="hud">
    <div class="stat-row">
      <div class="stat" id="hud-health">&#10084; --/20</div>
      <div class="stat" id="hud-food">&#x1F357; --/20</div>
      <div class="stat" id="hud-xp">&#10024; Lv --</div>
    </div>
    <div id="inv-bar"><span style="color:#666;font-size:12px;padding:0 8px">connecting…</span></div>
  </div>

  <div id="conn-dot"></div>

  <script>
    const dot      = document.getElementById('conn-dot');
    const hHealth  = document.getElementById('hud-health');
    const hFood    = document.getElementById('hud-food');
    const hXp      = document.getElementById('hud-xp');
    const hInv     = document.getElementById('inv-bar');

    function esc(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    async function poll() {
      try {
        const s = await fetch('/state').then(r => r.json());
        if (!s || !s.connected) { dot.className = 'err'; return; }

        dot.className = 'ok';
        hHealth.textContent = '\\u2764 ' + Number(s.health).toFixed(1) + '/20';
        hFood.textContent   = '\\uD83C\\uDF57 ' + s.food + '/20';
        hXp.textContent     = '\\u2728 Lv ' + s.xp;

        if (s.inventory && s.inventory.length > 0) {
          hInv.innerHTML = s.inventory
            .map(i =>
              '<div class="slot">'
              + '<div class="sname">' + esc(i.name.replace(/_/g, ' ')) + '</div>'
              + '<div class="scnt">' + esc(i.count) + '</div>'
              + '</div>'
            ).join('');
        } else {
          hInv.innerHTML = '<span style="color:#666;font-size:12px;padding:0 8px">inventory empty</span>';
        }
      } catch (_e) {
        dot.className = 'err';
      }
    }

    poll();
    setInterval(poll, 1500);
  </script>
</body>
</html>`;
}

export function startHud(bot: Bot): void {
  // Snapshot immediately, then wire up event-driven updates
  captureState(bot);

  bot.on("health", () => captureState(bot));
  bot.on("playerCollect", () => captureState(bot));
  // windowClose / windowOpen may not exist on all mineflayer versions; cast to any to be safe
  const b = bot as unknown as { on: (event: string, cb: () => void) => void };
  b.on("windowClose", () => captureState(bot));
  b.on("windowOpen", () => captureState(bot));

  // Fallback poll every 2 s to catch any state the events might miss
  const timer = setInterval(() => captureState(bot), 2000);
  bot.on("end", () => {
    clearInterval(timer);
    cachedState = { ...cachedState, connected: false };
  });

  const server = http.createServer((req, res) => {
    const url = req.url ?? "/";

    if (url === "/state") {
      const body = JSON.stringify(cachedState);
      res.writeHead(200, {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-store",
      });
      res.end(body);
      return;
    }

    if (url === "/" || url === "/hud") {
      const body = htmlPage();
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(body);
      return;
    }

    res.writeHead(404);
    res.end("Not found");
  });

  server.listen(HUD_PORT, () => {
    console.error(`[hud] server started`);
    console.error(`[hud]   live view + overlay → http://localhost:${HUD_PORT}/`);
    console.error(`[hud]   raw state JSON      → http://localhost:${HUD_PORT}/state`);
  });

  server.on("error", (err) => {
    console.error(`[hud] server error: ${err.message}`);
  });
}
