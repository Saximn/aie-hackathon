"use client";

import { useEffect, useRef, useState } from "react";
import { Panel } from "./Panel";

const WS_URL = process.env.NEXT_PUBLIC_BRAIN_WS_URL ?? "ws://localhost:8000/ws";

interface AgentEvent {
  event_type: string;
  cycle?: number | null;
  timestamp?: string;
  data: Record<string, unknown>;
  _localId?: string;
}

function rowColor(eventType: string): string {
  if (
    eventType === "failure_diagnosed" ||
    eventType === "verification_completed"
  ) {
    return ""; // handled below per-event
  }
  return "";
}

function verdictOf(event: AgentEvent): string | null {
  if (event.event_type !== "verification_completed") return null;
  const v = event.data.verdict as Record<string, string> | undefined;
  return v?.verdict ?? null;
}

function formatTs(iso: string | undefined): string {
  if (!iso) return "--:--:--";
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

function DataPreview({ data }: { data: Record<string, unknown> }) {
  const [open, setOpen] = useState(false);
  const preview = JSON.stringify(data);
  const truncated = preview.length > 80 ? preview.slice(0, 80) + "…" : preview;

  if (preview === "{}") return null;

  return (
    <div style={{ marginTop: 3 }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          background: "transparent",
          border: "none",
          color: "var(--muted)",
          cursor: "pointer",
          padding: 0,
          fontSize: 10,
          fontFamily: "var(--font-mono)",
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        <span>{open ? "▾" : "▸"}</span>
        {open ? "hide payload" : truncated}
      </button>
      {open && (
        <pre
          style={{
            background: "var(--code-bg)",
            padding: "6px 8px",
            borderRadius: 4,
            fontSize: 10,
            marginTop: 4,
            maxHeight: 160,
            overflow: "auto",
            boxShadow: "rgba(0,0,0,0.5) 0px 0px 0px 1px",
            lineHeight: 1.5,
          }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

export function ExecutionLog() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [filter, setFilter] = useState<"all" | "errors" | "skills">("all");
  const counterRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    let retryTimeout: ReturnType<typeof setTimeout>;

    function connect() {
      if (cancelled) return;
      let ws: WebSocket;
      try {
        ws = new WebSocket(WS_URL);
      } catch {
        if (!cancelled) retryTimeout = setTimeout(connect, 4000);
        return;
      }

      ws.onopen = () => {
        if (!cancelled) setConnected(true);
      };

      ws.onmessage = (msg: MessageEvent) => {
        try {
          const event: AgentEvent = JSON.parse(msg.data as string);
          event._localId = String(++counterRef.current);
          if (!cancelled) {
            setEvents((prev) => [...prev.slice(-499), event]);
          }
        } catch { /* ignore */ }
      };

      ws.onclose = () => {
        if (!cancelled) {
          setConnected(false);
          retryTimeout = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => ws.close();
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(retryTimeout);
    };
  }, []);

  const filtered = events.filter((e) => {
    if (filter === "errors")
      return (
        e.event_type === "failure_diagnosed" ||
        verdictOf(e) === "failed"
      );
    if (filter === "skills")
      return (
        e.event_type === "skill_candidate_created" ||
        e.event_type === "skill_promoted"
      );
    return true;
  });

  const subtitle = `${filtered.length}${filter !== "all" ? ` ${filter}` : ""} events`;

  return (
    <Panel title="Execution log" subtitle={subtitle}>
      {/* Filter tabs */}
      <div
        style={{
          display: "flex",
          gap: 4,
          marginBottom: 10,
          padding: "0 0 8px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        {(["all", "errors", "skills"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: "3px 10px",
              borderRadius: 9999,
              border: "none",
              fontSize: 11,
              fontWeight: filter === f ? 600 : 400,
              background:
                filter === f
                  ? "rgba(79,156,255,0.15)"
                  : "rgba(255,255,255,0.04)",
              color: filter === f ? "var(--accent)" : "var(--muted)",
              cursor: "pointer",
              transition: "background 0.15s",
            }}
          >
            {f}
          </button>
        ))}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
          <span
            style={{
              display: "inline-block",
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: connected ? "var(--success)" : "var(--danger)",
            }}
          />
          <span
            style={{
              fontSize: 10,
              color: "var(--muted)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {connected ? "live" : "offline"}
          </span>
        </div>
      </div>

      {/* Event list (newest first) */}
      <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {filtered.length === 0 ? (
          <div style={{ color: "var(--muted)", fontSize: 12, padding: "8px 0" }}>
            No events yet.
          </div>
        ) : (
          [...filtered].reverse().map((event) => {
            const verdict = verdictOf(event);
            const isError =
              event.event_type === "failure_diagnosed" ||
              verdict === "failed";
            const isSuccess =
              event.event_type === "skill_promoted" ||
              verdict === "success";

            const typeColor = isError
              ? "var(--danger)"
              : isSuccess
                ? "var(--success)"
                : event.event_type === "plan_created"
                  ? "#de1d8d"
                  : event.event_type === "goal_received"
                    ? "var(--accent)"
                    : "var(--muted)";

            return (
              <div
                key={event._localId}
                style={{
                  padding: "5px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.03)",
                  background: isError
                    ? "rgba(240,100,100,0.04)"
                    : "transparent",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      color: typeColor,
                      fontSize: 10,
                      fontWeight: 600,
                      fontFamily: "var(--font-mono)",
                      textTransform: "uppercase",
                      letterSpacing: "0.3px",
                    }}
                  >
                    {event.event_type}
                  </span>
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      flexShrink: 0,
                    }}
                  >
                    {event.cycle != null && (
                      <span
                        style={{
                          fontSize: 10,
                          color: "var(--muted)",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        c{event.cycle}
                      </span>
                    )}
                    <span
                      style={{
                        fontSize: 10,
                        color: "var(--muted)",
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {formatTs(event.timestamp)}
                    </span>
                  </div>
                </div>
                <DataPreview data={event.data} />
              </div>
            );
          })
        )}
      </div>
    </Panel>
  );
}
