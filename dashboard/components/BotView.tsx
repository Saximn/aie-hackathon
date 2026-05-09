"use client";

import { useQuery } from "convex/react";
import { api } from "../lib/convex_api";
import { Panel } from "./Panel";

const VIEW_RADIUS = 8;
const CELL = 18;

interface NearbyCount {
  name: string;
  count: number;
}

export function BotView() {
  const state = useQuery(api.state.latest);
  const symbolic = (state?.symbolic ?? null) as
    | {
        position?: { x: number; y: number; z: number } | null;
        biome?: string | null;
        health?: number | null;
        hunger?: number | null;
        nearby_blocks?: string[];
        nearbyBlocks?: string[];
      }
    | null;

  const nearby = symbolic
    ? (symbolic.nearby_blocks ?? symbolic.nearbyBlocks ?? []).map(parseNearby)
    : [];
  const position = symbolic?.position;

  return (
    <Panel
      title="Bot view (top-down)"
      subtitle={
        position
          ? `pos (${Math.round(position.x)}, ${Math.round(position.y)}, ${Math.round(position.z)}) — biome ${symbolic?.biome ?? "?"}`
          : "waiting for first observation…"
      }
    >
      <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
        <svg width={CELL * (VIEW_RADIUS * 2 + 1)} height={CELL * (VIEW_RADIUS * 2 + 1)}>
          {drawGrid()}
          {drawBotMarker()}
        </svg>
        <div style={{ flex: 1 }}>
          <Stat label="HP" value={symbolic?.health ?? null} max={20} colorScale={[0, 5, 10]} />
          <Stat label="Hunger" value={symbolic?.hunger ?? null} max={20} colorScale={[0, 5, 10]} />
          <h4 style={{ margin: "16px 0 8px", fontSize: 12, color: "var(--muted)", textTransform: "uppercase" }}>
            Nearby blocks
          </h4>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {nearby.slice(0, 12).map((n) => (
              <li
                key={n.name}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 12,
                  padding: "2px 0"
                }}
              >
                <span style={{ color: blockColor(n.name) }}>{n.name}</span>
                <span style={{ color: "var(--muted)" }}>{n.count}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Panel>
  );
}

function parseNearby(entry: string): NearbyCount {
  const idx = entry.lastIndexOf(":");
  if (idx === -1) return { name: entry, count: 1 };
  const count = Number.parseInt(entry.slice(idx + 1), 10);
  return { name: entry.slice(0, idx), count: Number.isFinite(count) ? count : 1 };
}

function drawGrid() {
  const cells = [];
  for (let x = 0; x < VIEW_RADIUS * 2 + 1; x++) {
    for (let y = 0; y < VIEW_RADIUS * 2 + 1; y++) {
      const dx = x - VIEW_RADIUS;
      const dy = y - VIEW_RADIUS;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const fill = dist > VIEW_RADIUS ? "transparent" : "rgba(79,156,255,0.04)";
      cells.push(
        <rect
          key={`${x}-${y}`}
          x={x * CELL}
          y={y * CELL}
          width={CELL - 1}
          height={CELL - 1}
          fill={fill}
          stroke="rgba(255,255,255,0.04)"
        />
      );
    }
  }
  return cells;
}

function drawBotMarker() {
  const cx = VIEW_RADIUS * CELL + CELL / 2;
  const cy = VIEW_RADIUS * CELL + CELL / 2;
  return (
    <g>
      <circle cx={cx} cy={cy} r={CELL / 2} fill="var(--accent)" />
      <circle cx={cx} cy={cy} r={CELL} fill="rgba(79,156,255,0.15)" stroke="var(--accent)" strokeOpacity={0.4} />
    </g>
  );
}

function Stat({
  label,
  value,
  max,
  colorScale
}: {
  label: string;
  value: number | null;
  max: number;
  colorScale: [number, number, number];
}) {
  if (value == null) {
    return (
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontSize: 12, color: "var(--muted)" }}>{label}</div>
        <div style={{ fontSize: 13 }}>—</div>
      </div>
    );
  }
  const ratio = Math.max(0, Math.min(1, value / max));
  let color = "var(--success)";
  if (value <= colorScale[0]) color = "var(--danger)";
  else if (value <= colorScale[1]) color = "var(--danger)";
  else if (value <= colorScale[2]) color = "var(--warn)";
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
        <span style={{ color: "var(--muted)" }}>{label}</span>
        <span>{value.toFixed(1)} / {max}</span>
      </div>
      <div
        style={{
          marginTop: 4,
          height: 6,
          background: "var(--code-bg)",
          borderRadius: 3,
          overflow: "hidden"
        }}
      >
        <div style={{ width: `${ratio * 100}%`, height: "100%", background: color }} />
      </div>
    </div>
  );
}

const BLOCK_COLOR_MAP: Record<string, string> = {
  oak_log: "#a07a4a",
  birch_log: "#d6cfa3",
  spruce_log: "#5a432a",
  stone: "#8a8a8a",
  cobblestone: "#7a7a7a",
  dirt: "#7a5a3a",
  grass_block: "#6fae5e",
  sand: "#e3d8a4",
  water: "#4f9cff",
  iron_ore: "#bfa07a",
  coal_ore: "#3a3a3a"
};

function blockColor(name: string): string {
  return BLOCK_COLOR_MAP[name] ?? "var(--text)";
}
