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

const EVENT_META: Record<
  string,
  { color: string; icon: string; label: string }
> = {
  goal_received:           { color: "#4f9cff", icon: "◎", label: "New Goal" },
  world_observed:          { color: "#666e7a", icon: "◈", label: "Observed" },
  memory_retrieved:        { color: "#666e7a", icon: "⬡", label: "Memory" },
  plan_created:            { color: "#de1d8d", icon: "◆", label: "Plan" },
  action_started:          { color: "#9aa3ad", icon: "▶", label: "Action Start" },
  action_completed:        { color: "#9aa3ad", icon: "◼", label: "Action Done" },
  verification_completed:  { color: "#4fd18a", icon: "✓", label: "Verified" },
  failure_diagnosed:       { color: "#f06464", icon: "✗", label: "Failure" },
  skill_candidate_created: { color: "#f1c358", icon: "⬟", label: "Skill Draft" },
  skill_promoted:          { color: "#4fd18a", icon: "★", label: "Skill Saved" },
};

function eventSummary(event: AgentEvent): string | null {
  const d = event.data;
  switch (event.event_type) {
    case "goal_received":
      return String(d.task ?? d.goal ?? "");
    case "plan_created":
      return String(d.explain ?? "");
    case "verification_completed": {
      const v = d.verdict as Record<string, string> | undefined;
      return v ? `${v.verdict}: ${v.feedback}` : null;
    }
    case "skill_candidate_created":
    case "skill_promoted": {
      const s = d.skill as Record<string, string> | undefined;
      return s?.name ?? null;
    }
    case "action_completed": {
      const e = d.execution as Record<string, string> | undefined;
      return e?.result ?? null;
    }
    case "failure_diagnosed": {
      const diag = d.diagnosis as Record<string, string> | undefined;
      return diag?.cause ?? null;
    }
    default:
      return null;
  }
}

function formatTs(iso: string | undefined): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "";
  }
}

export function AgentThoughtStream() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const counterRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    let retryTimeout: ReturnType<typeof setTimeout>;

    function connect() {
      if (cancelled) return;
      setReconnecting(false);

      let ws: WebSocket;
      try {
        ws = new WebSocket(WS_URL);
      } catch {
        if (!cancelled) {
          setReconnecting(true);
          retryTimeout = setTimeout(connect, 4000);
        }
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
            setEvents((prev) => [...prev.slice(-299), event]);
          }
        } catch {
          /* ignore malformed frames */
        }
      };

      ws.onclose = () => {
        if (!cancelled) {
          setConnected(false);
          setReconnecting(true);
          retryTimeout = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(retryTimeout);
    };
  }, []);

  // Auto-scroll to bottom on new events
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  const dotColor = connected
    ? "var(--success)"
    : reconnecting
      ? "var(--warn)"
      : "var(--danger)";

  const subtitle = connected
    ? `${events.length} events`
    : reconnecting
      ? "reconnecting…"
      : "disconnected — start brain with python -m main";

  return (
    <Panel title="Agent thought stream" subtitle={subtitle}>
      {/* Live indicator dot */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 10,
          fontSize: 11,
          color: "var(--muted)",
          fontFamily: "var(--font-mono)",
        }}
      >
        <span
          style={{
            display: "inline-block",
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: dotColor,
            boxShadow: connected ? `0 0 6px ${dotColor}` : "none",
          }}
        />
        {connected ? "LIVE · ws://localhost:8000/ws" : reconnecting ? "RECONNECTING…" : "DISCONNECTED"}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {events.length === 0 ? (
          <div
            style={{
              color: "var(--muted)",
              fontSize: 13,
              padding: "12px 0",
              textAlign: "center",
            }}
          >
            {connected
              ? "Waiting for agent events…"
              : "Start the agent loop: python -m run_agent --demo"}
          </div>
        ) : (
          events.map((event) => {
            const meta = EVENT_META[event.event_type] ?? {
              color: "var(--muted)",
              icon: "○",
              label: event.event_type,
            };
            const summary = eventSummary(event);
            const isError =
              event.event_type === "failure_diagnosed" ||
              (event.event_type === "verification_completed" &&
                (event.data.verdict as Record<string, string> | undefined)
                  ?.verdict === "failed");
            const isPlan = event.event_type === "plan_created";
            const steps = isPlan
              ? (event.data.steps as string[] | undefined) ?? []
              : [];
            const code = isPlan ? (event.data.code as string | undefined) : null;

            return (
              <div
                key={event._localId}
                style={{
                  display: "flex",
                  gap: 8,
                  padding: "6px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.04)",
                  alignItems: "flex-start",
                  background: isError
                    ? "rgba(240,100,100,0.04)"
                    : "transparent",
                  borderRadius: isError ? 4 : 0,
                }}
              >
                {/* Icon */}
                <span
                  style={{
                    color: meta.color,
                    fontSize: 13,
                    lineHeight: "18px",
                    flexShrink: 0,
                    width: 14,
                    textAlign: "center",
                    marginTop: 1,
                  }}
                >
                  {meta.icon}
                </span>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 8,
                      alignItems: "baseline",
                    }}
                  >
                    <span
                      style={{
                        color: meta.color,
                        fontSize: 11,
                        fontWeight: 600,
                        fontFamily: "var(--font-mono)",
                        textTransform: "uppercase",
                        letterSpacing: "0.3px",
                      }}
                    >
                      {meta.label}
                    </span>
                    <div
                      style={{
                        display: "flex",
                        gap: 8,
                        alignItems: "baseline",
                        flexShrink: 0,
                      }}
                    >
                      {event.cycle != null && (
                        <span
                          style={{
                            color: "var(--muted)",
                            fontSize: 10,
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          c{event.cycle}
                        </span>
                      )}
                      <span
                        style={{
                          color: "var(--muted)",
                          fontSize: 10,
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        {formatTs(event.timestamp)}
                      </span>
                    </div>
                  </div>

                  {summary && (
                    <div
                      style={{
                        color: "var(--text)",
                        fontSize: 12,
                        marginTop: 2,
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-word",
                        opacity: 0.9,
                        lineHeight: 1.5,
                      }}
                    >
                      {summary.length > 300
                        ? summary.slice(0, 300) + "…"
                        : summary}
                    </div>
                  )}

                  {steps.length > 0 && (
                    <ol
                      style={{
                        margin: "4px 0 0 16px",
                        padding: 0,
                        fontSize: 11,
                        color: "var(--muted)",
                        lineHeight: 1.6,
                      }}
                    >
                      {steps.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                  )}

                  {code && (
                    <pre
                      style={{
                        background: "var(--code-bg)",
                        padding: "6px 8px",
                        borderRadius: 6,
                        fontSize: 11,
                        marginTop: 6,
                        maxHeight: 140,
                        overflow: "auto",
                        boxShadow: "rgba(0,0,0,0.5) 0px 0px 0px 1px",
                        lineHeight: 1.5,
                      }}
                    >
                      {String(code).slice(0, 800)}
                    </pre>
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </Panel>
  );
}
