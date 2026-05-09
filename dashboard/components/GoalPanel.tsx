"use client";

import { useQuery } from "convex/react";
import { api } from "../lib/convex_api";
import { Panel } from "./Panel";

export function GoalPanel() {
  const events = useQuery(api.events.recent, { limit: 100 });
  if (!events) {
    return (
      <Panel title="Current goal" subtitle="loading…">
        <div style={{ color: "var(--muted)" }}>connecting to Convex…</div>
      </Panel>
    );
  }

  const goalEvent = findLatest(events, "goal_received");
  const planEvent = findLatest(events, "plan_created");
  const verdictEvent = findLatest(events, "verification_completed");

  const task = goalEvent?.data?.task ?? "(no goal yet)";
  const rationale = goalEvent?.data?.rationale ?? "";
  const explain = planEvent?.data?.explain ?? "";
  const steps: string[] = planEvent?.data?.steps ?? [];
  const code: string = planEvent?.data?.action?.code ?? "";
  const verdict = verdictEvent?.data?.verdict?.verdict ?? null;
  const feedback = verdictEvent?.data?.verdict?.feedback ?? "";

  return (
    <Panel title="Current goal" subtitle={rationale || undefined}>
      <h2 style={{ margin: "0 0 8px", fontSize: 16 }}>{task}</h2>
      {verdict ? <Verdict verdict={verdict} feedback={feedback} /> : null}
      {explain ? (
        <p style={{ margin: "12px 0", color: "var(--muted)" }}>{explain}</p>
      ) : null}
      {steps.length > 0 ? (
        <ol style={{ margin: "8px 0 12px 20px", padding: 0, color: "var(--text)" }}>
          {steps.map((step, idx) => (
            <li key={idx} style={{ marginBottom: 4, fontSize: 13 }}>
              {step}
            </li>
          ))}
        </ol>
      ) : null}
      {code ? (
        <pre
          style={{
            background: "var(--code-bg)",
            padding: 12,
            borderRadius: 8,
            margin: 0,
            maxHeight: 220,
            overflow: "auto",
            border: "1px solid var(--panel-border)"
          }}
        >
          {code}
        </pre>
      ) : null}
    </Panel>
  );
}

function Verdict({ verdict, feedback }: { verdict: string; feedback: string }) {
  const palette: Record<string, string> = {
    success: "var(--success)",
    incomplete: "var(--warn)",
    failed: "var(--danger)"
  };
  return (
    <div
      style={{
        display: "inline-flex",
        gap: 8,
        alignItems: "center",
        padding: "4px 10px",
        background: "var(--code-bg)",
        border: `1px solid ${palette[verdict] ?? "var(--panel-border)"}`,
        borderRadius: 999,
        fontSize: 12
      }}
    >
      <span style={{ color: palette[verdict] ?? "var(--text)", fontWeight: 600 }}>
        {verdict}
      </span>
      <span style={{ color: "var(--muted)" }}>{feedback}</span>
    </div>
  );
}

function findLatest(events: { eventType: string; data: any }[], type: string) {
  return events.find((e) => e.eventType === type);
}
