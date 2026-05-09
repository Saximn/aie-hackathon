"use client";

import { useEffect, useRef, useState } from "react";
import {
  fetchMetrics,
  fetchStatus,
  type MetricsResponse,
  type StatusResponse,
} from "../lib/brain";
import type { AgentEvent } from "../lib/brain";
import { Skeleton } from "./ui";

interface Tile {
  label: string;
  value: string;
  /** Whatever numeric the trend should compare against. */
  numeric?: number | null;
  hint?: string;
}

export interface MetricsRibbonProps {
  /** WS event stream — used to compute success-rate and skill counts client-side. */
  events?: AgentEvent[];
  /** Test injection. */
  initialMetrics?: MetricsResponse | null;
  initialStatus?: StatusResponse | null;
}

function avgCycleMsFromEvents(events: AgentEvent[]): number | null {
  const samples: number[] = [];
  for (const e of events) {
    if (e.event_type === "action_completed") {
      const wall =
        (e.data.wallMs as number | undefined) ??
        (e.data.durationMs as number | undefined);
      if (typeof wall === "number") samples.push(wall);
    }
  }
  if (samples.length === 0) return null;
  return Math.round(samples.reduce((a, b) => a + b, 0) / samples.length);
}

function successRateFromEvents(events: AgentEvent[]): {
  pct: number | null;
  total: number;
} {
  let success = 0;
  let total = 0;
  for (const e of events) {
    if (e.event_type !== "verification_completed") continue;
    const v = (e.data.verdict as Record<string, string> | string | undefined);
    const verdict =
      typeof v === "string" ? v : (v?.verdict ?? null);
    if (!verdict) continue;
    total += 1;
    if (verdict === "success") success += 1;
  }
  if (total === 0) return { pct: null, total: 0 };
  return { pct: Math.round((success / total) * 100), total };
}

function skillCountFromEvents(events: AgentEvent[]): number {
  const seen = new Set<string>();
  for (const e of events) {
    if (
      e.event_type === "skill_promoted" ||
      e.event_type === "skill_candidate_created"
    ) {
      const skill = e.data.skill as Record<string, string> | undefined;
      const name = skill?.name ?? (e.data.name as string | undefined);
      if (name) seen.add(name);
    }
  }
  return seen.size;
}

function episodeCountFromEvents(events: AgentEvent[]): number {
  // Each top-level goal_received marks a new episode (closest match in event_bus.py).
  return events.filter((e) => e.event_type === "goal_received").length;
}

export function MetricsRibbon({
  events = [],
  initialMetrics = null,
  initialStatus = null,
}: MetricsRibbonProps) {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(initialMetrics);
  const [status, setStatus] = useState<StatusResponse | null>(initialStatus);

  // Trend memory — previous numeric values used for arrows.
  const prevRef = useRef<Record<string, number | null>>({});

  useEffect(() => {
    if (initialMetrics !== null || initialStatus !== null) return;
    let stop = false;
    const poll = async () => {
      try {
        const [m, s] = await Promise.all([fetchMetrics(), fetchStatus()]);
        if (stop) return;
        setMetrics(m);
        setStatus(s);
      } catch {
        /* noop — chrome shouldn't error visually */
      }
    };
    poll();
    const id = setInterval(poll, 2000);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, [initialMetrics, initialStatus]);

  const avgMs = avgCycleMsFromEvents(events);
  const { pct: successPct, total: verificationTotal } =
    successRateFromEvents(events);
  const skillCount = skillCountFromEvents(events);
  const episodeCount = Math.max(
    episodeCountFromEvents(events),
    status?.cycle ?? 0,
  );

  const tiles: Tile[] = [
    {
      label: "avg cycle",
      value: avgMs == null ? "—" : `${avgMs}ms`,
      numeric: avgMs,
      hint: "average action wall time",
    },
    {
      label: "success rate",
      value:
        successPct == null
          ? "—"
          : `${successPct}%`,
      numeric: successPct,
      hint:
        verificationTotal > 0
          ? `${verificationTotal} verifications`
          : "no verifications yet",
    },
    {
      label: "skills",
      value: String(skillCount || metrics?.recent_skills?.length || 0),
      numeric: skillCount,
      hint: "learned + candidates",
    },
    {
      label: "episodes",
      value: String(episodeCount || 0),
      numeric: episodeCount,
      hint: "goals received",
    },
  ];

  // Capture trend snapshots after render
  useEffect(() => {
    const next: Record<string, number | null> = {};
    tiles.forEach((t) => {
      next[t.label] = t.numeric ?? null;
    });
    prevRef.current = next;
  });

  if (metrics === null && events.length === 0 && initialMetrics === null) {
    return (
      <div
        className="panel panel-flat"
        style={{
          padding: "var(--sp-3)",
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "var(--sp-3)",
        }}
        aria-label="Loading metrics"
      >
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} height={48} />
        ))}
      </div>
    );
  }

  return (
    <div
      className="panel panel-flat"
      role="region"
      aria-label="Metrics overview"
      style={{
        padding: "var(--sp-3) var(--sp-4)",
        display: "grid",
        gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
        gap: "var(--sp-4)",
      }}
    >
      {tiles.map((t) => {
        const prev = prevRef.current[t.label];
        const trend =
          t.numeric != null && prev != null && prev !== t.numeric
            ? t.numeric > prev
              ? "up"
              : "down"
            : null;
        return (
          <div key={t.label} className="col" style={{ gap: 4, minWidth: 0 }}>
            <span className="t-label">{t.label}</span>
            <div
              className="row-tight"
              style={{
                gap: 6,
                fontSize: "var(--t-20)",
                fontWeight: 600,
                color: "var(--text)",
                fontVariantNumeric: "tabular-nums",
                letterSpacing: "var(--track-20)",
                lineHeight: 1.1,
              }}
            >
              <span className="truncate" title={t.value}>
                {t.value}
              </span>
              {trend === "up" && (
                <span aria-label="trending up" style={{ color: "var(--success)", fontSize: "var(--t-12)" }}>
                  ↑
                </span>
              )}
              {trend === "down" && (
                <span aria-label="trending down" style={{ color: "var(--text-tertiary)", fontSize: "var(--t-12)" }}>
                  ↓
                </span>
              )}
            </div>
            {t.hint && (
              <span
                style={{
                  fontSize: "var(--t-11)",
                  color: "var(--text-tertiary)",
                }}
              >
                {t.hint}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
