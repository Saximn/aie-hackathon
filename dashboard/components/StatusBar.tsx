"use client";

import { useEffect, useState } from "react";
import {
  fetchStatus,
  fetchMetrics,
  type MetricsResponse,
  type StatusResponse,
} from "../lib/brain";
import { LiveDot, Pill, type PillTone } from "./ui";

function formatUptime(s: number): string {
  if (!Number.isFinite(s) || s < 0) return "—";
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

function verdictTone(verdict: string | null | undefined): PillTone {
  if (verdict === "success") return "success";
  if (verdict === "failed") return "danger";
  if (verdict === "incomplete" || verdict === "stuck") return "warning";
  return "neutral";
}

function verdictIcon(verdict: string | null | undefined) {
  if (verdict === "success") return "✓";
  if (verdict === "failed") return "✗";
  if (verdict === "incomplete" || verdict === "stuck") return "!";
  return "·";
}

export interface StatusBarProps {
  /** Inject mocks for tests. When set, polling is skipped. */
  initialStatus?: StatusResponse | null;
  initialMetrics?: MetricsResponse | null;
  /** Connection state from the WS hook (drives the live dot). */
  connection?: "open" | "connecting" | "reconnecting" | "closed";
}

export function StatusBar({
  initialStatus = null,
  initialMetrics = null,
  connection,
}: StatusBarProps) {
  const [status, setStatus] = useState<StatusResponse | null>(initialStatus);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(initialMetrics);
  const [error, setError] = useState(false);

  useEffect(() => {
    // When tests inject `initialStatus`, treat as static (no polling).
    if (initialStatus !== null || initialMetrics !== null) return;
    let stop = false;
    const poll = async () => {
      try {
        const [s, m] = await Promise.all([fetchStatus(), fetchMetrics()]);
        if (stop) return;
        setStatus(s);
        setMetrics(m);
        setError(false);
      } catch {
        if (!stop) setError(true);
      }
    };
    poll();
    const id = setInterval(poll, 2000);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, [initialStatus, initialMetrics]);

  const isOnline =
    connection === "open" || (!error && (status?.running ?? false));

  const dotTone: "success" | "warning" | "danger" =
    error ? "danger" : isOnline ? "success" : "warning";

  return (
    <header
      className="panel panel-flat"
      role="banner"
      aria-label="Agent status"
      style={{
        flexDirection: "row",
        alignItems: "center",
        gap: "var(--sp-4)",
        padding: "var(--sp-2) var(--sp-4)",
        minHeight: 44,
        flexWrap: "nowrap",
      }}
    >
      {/* Brand + live dot */}
      <div className="row-tight" style={{ flexShrink: 0 }}>
        <span
          style={{
            fontSize: "var(--t-14)",
            fontWeight: 600,
            letterSpacing: "var(--track-16)",
            color: "var(--text)",
          }}
        >
          OmniPlay-MC
        </span>
        <LiveDot
          tone={dotTone}
          pulse={isOnline}
          ariaLabel={
            error ? "Brain offline" : isOnline ? "Live" : "Idle"
          }
        />
        <span className="t-label" style={{ color: dotTone === "success" ? "var(--success)" : "var(--text-tertiary)" }}>
          {error ? "offline" : isOnline ? "live" : "idle"}
        </span>
      </div>

      {/* Goal — single dominant line, truncated */}
      <div
        className="row-tight"
        style={{ flex: 1, minWidth: 0, gap: "var(--sp-2)" }}
      >
        <span className="t-label">goal</span>
        <span
          className="truncate"
          style={{
            fontSize: "var(--t-14)",
            color: status?.currentGoal
              ? "var(--text)"
              : "var(--text-tertiary)",
            fontWeight: 500,
          }}
          title={status?.currentGoal ?? "no active goal"}
        >
          {status?.currentGoal ?? "no active goal"}
        </span>
      </div>

      {/* Right cluster — chips */}
      <div className="row" style={{ gap: "var(--sp-4)", flexShrink: 0 }}>
        <Stat label="cycle" value={String(metrics?.total_cycles ?? status?.cycle ?? 0)} />
        <Stat label="uptime" value={metrics ? formatUptime(metrics.uptime_seconds) : "—"} />
        {metrics?.last_verdict ? (
          <Pill
            tone={verdictTone(metrics.last_verdict)}
            icon={verdictIcon(metrics.last_verdict)}
          >
            {metrics.last_verdict}
          </Pill>
        ) : (
          <Pill tone="neutral" icon="·">no verdict</Pill>
        )}
        {(metrics?.queued_tasks ?? 0) > 0 && (
          <Pill tone="warning" icon="↳">
            queue {metrics?.queued_tasks}
          </Pill>
        )}
      </div>
    </header>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="row-tight" style={{ gap: 6 }}>
      <span className="t-label">{label}</span>
      <span
        className="t-num"
        style={{
          fontSize: "var(--t-14)",
          fontWeight: 600,
          color: "var(--text)",
        }}
      >
        {value}
      </span>
    </div>
  );
}
