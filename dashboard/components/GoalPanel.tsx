"use client";

import type { AgentEvent } from "../lib/brain";
import { Panel } from "./ui/Panel";

export function GoalPanel({ events }: { events: AgentEvent[] }) {
  const goalEvent = findLatest(events, "goal_received");
  const planEvent = findLatest(events, "plan_created");
  const verdictEvent = findLatest(events, "verification_completed");

  const task = (goalEvent?.data?.task as string | undefined) ?? "(no goal yet)";
  const rationale = (goalEvent?.data?.rationale as string | undefined) ?? "";
  const explain = (planEvent?.data?.explain as string | undefined) ?? "";
  const steps: string[] = (planEvent?.data?.steps as string[] | undefined) ?? [];
  const code: string = (planEvent?.data?.action as { code?: string } | undefined)?.code ?? "";
  const verdict = (verdictEvent?.data?.verdict as { verdict?: string; feedback?: string } | undefined)?.verdict ?? null;
  const feedback = (verdictEvent?.data?.verdict as { verdict?: string; feedback?: string } | undefined)?.feedback ?? "";

  return (
    <Panel title="Current goal" trailing={rationale || undefined}>
      <h2 style={{ margin: "0 0 8px", fontSize: 16, letterSpacing: "-0.2px" }}>{task}</h2>
      {verdict ? <Verdict verdict={verdict} feedback={feedback} /> : null}
      {explain ? (
        <p style={{ margin: "12px 0", color: "var(--text-secondary)", fontSize: 13 }}>{explain}</p>
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
        <pre className="code-block" style={{ maxHeight: 220 }}>
          {code}
        </pre>
      ) : null}
      {!goalEvent && (
        <div className="empty-state">
          <div className="empty-state__hint">Waiting for first goal…</div>
        </div>
      )}
    </Panel>
  );
}

function Verdict({ verdict, feedback }: { verdict: string; feedback: string }) {
  const palette: Record<string, string> = {
    success: "var(--success)",
    incomplete: "var(--warning)",
    failed: "var(--danger)"
  };
  return (
    <div
      style={{
        display: "inline-flex",
        gap: 8,
        alignItems: "center",
        padding: "4px 10px",
        background: "var(--bg-overlay)",
        border: `1px solid ${palette[verdict] ?? "var(--ring)"}`,
        borderRadius: "var(--radius-pill)",
        fontSize: 12
      }}
    >
      <span style={{ color: palette[verdict] ?? "var(--text)", fontWeight: 600 }}>
        {verdict}
      </span>
      {feedback && <span style={{ color: "var(--text-secondary)" }}>{feedback}</span>}
    </div>
  );
}

function findLatest(events: AgentEvent[], type: string): AgentEvent | undefined {
  return [...events].reverse().find((e) => e.event_type === type);
}
