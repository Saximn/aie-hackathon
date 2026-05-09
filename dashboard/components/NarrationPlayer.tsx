"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "convex/react";
import { api } from "../lib/convex_api";

interface NarrationClip {
  _id: string;
  clipId: string;
  text: string;
  audioUrl?: string | null;
  createdAt: string;
}

export function NarrationPlayer() {
  const clips = useQuery(api.narration.latest, { limit: 5 }) as NarrationClip[] | undefined;
  const [muted, setMuted] = useState(false);
  const [playedIds, setPlayedIds] = useState<Set<string>>(() => new Set());
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const latest = clips?.[0];

  useEffect(() => {
    if (!latest || muted) return;
    if (!latest.audioUrl) return;
    if (playedIds.has(latest.clipId)) return;
    setPlayedIds(new Set([...playedIds, latest.clipId]));
    const audio = audioRef.current;
    if (audio) {
      audio.src = latest.audioUrl;
      audio.play().catch(() => {
        /* autoplay rejected; user can press play manually */
      });
    }
  }, [latest?.clipId, latest?.audioUrl, muted, playedIds]);

  const recent = useMemo(() => clips?.slice(0, 3) ?? [], [clips]);

  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--panel-border)",
        borderRadius: 12,
        padding: "10px 16px",
        display: "flex",
        gap: 16,
        alignItems: "center"
      }}
    >
      <button
        onClick={() => setMuted((m) => !m)}
        style={{
          background: "var(--code-bg)",
          border: "1px solid var(--panel-border)",
          color: "var(--text)",
          padding: "6px 12px",
          borderRadius: 6,
          cursor: "pointer"
        }}
      >
        {muted ? "Unmute narration" : "Mute"}
      </button>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ color: "var(--muted)", fontSize: 12 }}>Latest narration</div>
        <div style={{ fontSize: 13, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {latest?.text ?? "—"}
        </div>
      </div>
      <audio ref={audioRef} controls style={{ width: 240 }} />
      <details style={{ color: "var(--muted)", fontSize: 12 }}>
        <summary style={{ cursor: "pointer" }}>history</summary>
        <ul style={{ listStyle: "none", padding: 0, margin: "8px 0 0", maxWidth: 320 }}>
          {recent.map((c) => (
            <li key={c.clipId} style={{ padding: "2px 0" }}>
              {c.text}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
