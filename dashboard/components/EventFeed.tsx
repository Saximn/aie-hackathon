"use client";

import { useQuery } from "convex/react";
import { api } from "../lib/convex_api";
import { Panel } from "./Panel";

const EVENT_COLOR: Record<string, string> = {
  goal_received: "var(--accent)",
  world_observed: "var(--muted)",
  memory_retrieved: "var(--muted)",
  plan_created: "var(--accent)",
  action_started: "var(--text)",
  action_completed: "var(--text)",
  verification_completed: "var(--success)",
  failure_diagnosed: "var(--danger)",
  skill_candidate_created: "var(--success)",
  skill_promoted: "var(--success)"
};

export function EventFeed() {
  const events = useQuery(api.events.recent, { limit: 50 });
  if (!events) {
    return (
      <Panel title="Event feed" subtitle="loading…">
        <div style={{ color: "var(--muted)" }}>connecting…</div>
      </Panel>
    );
  }
  return (
    <Panel title="Event feed" subtitle={`${events.length} most recent`}>
      <ol style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {(events as Array<{ _id: string; eventType: string; cycle: number; timestamp: string; data: any }>).map((event) => (
          <li
            key={event._id}
            style={{
              padding: "6px 0",
              borderBottom: "1px solid var(--panel-border)",
              fontSize: 12
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
              <span style={{ color: EVENT_COLOR[event.eventType] ?? "var(--text)", fontWeight: 600 }}>
                {event.eventType}
              </span>
              <span style={{ color: "var(--muted)" }}>cycle {event.cycle}</span>
            </div>
            <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 2 }}>
              {formatTimestamp(event.timestamp)}
            </div>
            <Summary event={event} />
          </li>
        ))}
      </ol>
    </Panel>
  );
}

function Summary({ event }: { event: { eventType: string; data: any } }) {
  switch (event.eventType) {
    case "goal_received":
      return <Line>{event.data?.task}</Line>;
    case "plan_created":
      return <Line>{event.data?.explain}</Line>;
    case "verification_completed":
      return (
        <Line>
          {event.data?.verdict?.verdict}: {event.data?.verdict?.feedback}
        </Line>
      );
    case "failure_diagnosed":
      return <Line>{event.data?.diagnosis?.cause}</Line>;
    case "skill_candidate_created":
    case "skill_promoted":
      return <Line>{event.data?.skill?.name}</Line>;
    case "action_completed":
      return <Line>{event.data?.execution?.result}</Line>;
    default:
      return null;
  }
}

function Line({ children }: { children: React.ReactNode }) {
  if (!children) return null;
  return (
    <div
      style={{
        marginTop: 2,
        color: "var(--text)",
        fontSize: 12,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis"
      }}
    >
      {children}
    </div>
  );
}

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}
