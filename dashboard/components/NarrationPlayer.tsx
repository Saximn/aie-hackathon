"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { AgentEvent } from "../lib/brain";
import { narrationUrl } from "../lib/brain";

interface NarrationClip {
  clipId: string;
  text: string;
}

export function NarrationPlayer({ events }: { events: AgentEvent[] }) {
  // Collect narration events from the shared WebSocket stream, most-recent first.
  const clips = useMemo<NarrationClip[]>(() => {
    return [...events]
      .reverse()
      .filter((e) => e.event_type === "narration" && e.data?.clip_id)
      .slice(0, 5)
      .map((e) => ({
        clipId: String(e.data.clip_id),
        text: String(e.data.text ?? ""),
      }));
  }, [events]);

  const [muted, setMuted] = useState(false);
  const [playedIds, setPlayedIds] = useState<Set<string>>(() => new Set());
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const latest = clips[0];

  useEffect(() => {
    if (!latest || muted) return;
    if (playedIds.has(latest.clipId)) return;
    setPlayedIds((prev) => new Set([...prev, latest.clipId]));
    const audio = audioRef.current;
    if (audio) {
      audio.src = narrationUrl(latest.clipId);
      audio.play().catch(() => {
        /* autoplay policy may block; user can press play manually */
      });
    }
  }, [latest?.clipId, muted, playedIds]);

  const recent = clips.slice(0, 3);

  return (
    <div
      style={{
        background: "var(--bg-elevated)",
        borderRadius: "var(--radius-lg)",
        boxShadow: "var(--shadow-card)",
        padding: "10px 16px",
        display: "flex",
        gap: 12,
        alignItems: "center",
        flexShrink: 0,
      }}
    >
      <button
        onClick={() => setMuted((m) => !m)}
        className="btn btn-secondary btn-sm"
      >
        {muted ? "Unmute" : "Mute"}
      </button>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ color: "var(--text-tertiary)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em", fontFamily: "var(--font-mono)" }}>
          Narration
        </div>
        <div style={{ fontSize: 13, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", color: "var(--text)" }}>
          {latest?.text ?? "—"}
        </div>
      </div>
      <audio ref={audioRef} controls style={{ width: 200, flexShrink: 0 }} />
      {recent.length > 1 && (
        <details style={{ color: "var(--text-secondary)", fontSize: 12, flexShrink: 0 }}>
          <summary style={{ cursor: "pointer" }}>history</summary>
            <ul style={{ listStyle: "none", padding: "8px 12px", margin: "8px 0 0", maxWidth: 280, position: "absolute", background: "var(--bg-overlay)", boxShadow: "var(--shadow-popover)", borderRadius: "var(--radius-md)" }}>
            {recent.map((c) => (
              <li key={c.clipId} style={{ padding: "2px 0", fontSize: 12, color: "var(--text-secondary)" }}>
                {c.text}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
