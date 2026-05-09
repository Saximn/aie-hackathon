"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Panel, Pill, LiveDot, Tabs, EmptyState, ErrorState } from "./ui";
import type { TabItem, PillTone } from "./ui";
import {
  type AgentEvent,
  narrationUrl,
} from "../lib/brain";

type FilterId = "all" | "plans" | "skills" | "critic" | "errors";

const FILTERS: ReadonlyArray<TabItem<FilterId>> = [
  { value: "all", label: "All" },
  { value: "plans", label: "Plans" },
  { value: "skills", label: "Skills" },
  { value: "critic", label: "Critic" },
  { value: "errors", label: "Errors" },
];

/** Map an event to its workflow accent (DESIGN.md — used for category, not decoration). */
function accentForEvent(eventType: string): string {
  switch (eventType) {
    case "goal_received":
    case "user_instruction_received":
      return "var(--develop)";
    case "plan_created":
      return "var(--preview)";
    case "verification_completed":
    case "skill_promoted":
      return "var(--success)";
    case "failure_diagnosed":
      return "var(--ship)";
    case "skill_candidate_created":
      return "var(--warning)";
    default:
      return "var(--text-tertiary)";
  }
}

function labelForEvent(eventType: string): string {
  return eventType.replace(/_/g, " ");
}

function formatTime(ts: string | undefined): string {
  if (!ts) return "";
  try {
    return new Date(ts).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

function matchesFilter(evt: AgentEvent, filter: FilterId): boolean {
  if (filter === "all") return true;
  if (filter === "plans") return evt.event_type === "plan_created";
  if (filter === "skills")
    return (
      evt.event_type === "skill_promoted" ||
      evt.event_type === "skill_candidate_created"
    );
  if (filter === "critic") return evt.event_type === "verification_completed";
  if (filter === "errors")
    return (
      evt.event_type === "failure_diagnosed" ||
      (evt.event_type === "verification_completed" &&
        verdictOf(evt) === "failed")
    );
  return true;
}

function verdictOf(evt: AgentEvent): string | null {
  if (evt.event_type !== "verification_completed") return null;
  const v = evt.data.verdict as Record<string, string> | string | undefined;
  if (typeof v === "string") return v;
  return v?.verdict ?? null;
}

export interface AgentThoughtStreamProps {
  events: AgentEvent[];
  connection: "open" | "connecting" | "reconnecting" | "closed";
  onRetry?: () => void;
}

export function AgentThoughtStream({
  events,
  connection,
  onRetry,
}: AgentThoughtStreamProps) {
  const [filter, setFilter] = useState<FilterId>("all");
  const scrollerRef = useRef<HTMLDivElement>(null);
  const stickToBottomRef = useRef(true);
  const lastEventCountRef = useRef(0);

  // Slack-style auto-scroll: stay pinned to bottom unless user scrolls up.
  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    if (events.length > lastEventCountRef.current && stickToBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
    lastEventCountRef.current = events.length;
  }, [events.length]);

  const filtered = useMemo(
    () => events.filter((e) => matchesFilter(e, filter)),
    [events, filter],
  );

  const handleScroll = () => {
    const el = scrollerRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    stickToBottomRef.current = distance < 40;
  };

  const dotTone =
    connection === "open"
      ? "success"
      : connection === "reconnecting"
        ? "warning"
        : "danger";

  const trailing = (
    <div className="row-tight" style={{ gap: "var(--sp-2)" }}>
      <LiveDot tone={dotTone} pulse={connection === "open"} ariaLabel={connection} />
      <span className="t-label">
        {connection === "open"
          ? `live · ${events.length} events`
          : connection === "reconnecting"
            ? "reconnecting"
            : "disconnected"}
      </span>
    </div>
  );

  return (
    <Panel
      variant="primary"
      title="Agent thought stream"
      trailing={trailing}
      toolbar={
        <Tabs<FilterId>
          items={FILTERS}
          value={filter}
          onChange={setFilter}
        />
      }
      flush
    >
      <div
        ref={scrollerRef}
        onScroll={handleScroll}
        style={{
          flex: 1,
          minHeight: 0,
          overflow: "auto",
          padding: "var(--sp-4)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--sp-2)",
        }}
      >
        {connection === "closed" || (connection === "reconnecting" && events.length === 0) ? (
          <ErrorState
            message={
              <>
                Couldn’t reach the agent over <code>/ws</code>. Start the brain
                with <code>python -m main</code>.
              </>
            }
            onRetry={onRetry}
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            title={
              filter === "all"
                ? "Waiting for the first agent event…"
                : `No ${filter} events yet`
            }
            hint={
              filter === "all"
                ? "Send a task below to start a planning cycle. Each step the agent thinks, plans, and acts will stream here in real time."
                : "Switch filters or wait for the agent to produce one."
            }
          />
        ) : (
          filtered.map((evt) => <EventCard key={evt._localId ?? evt.id} event={evt} />)
        )}
      </div>
    </Panel>
  );
}

/* ----------------------------------------------------------------------------
 * Per-event card renderers
 * ------------------------------------------------------------------------- */

function EventCard({ event }: { event: AgentEvent }) {
  switch (event.event_type) {
    case "goal_received":
    case "user_instruction_received":
      return <GoalCard event={event} />;
    case "plan_created":
      return <PlanCard event={event} />;
    case "action_started":
      return <ActionStartedRow event={event} />;
    case "action_completed":
      return <ActionCompletedRow event={event} />;
    case "verification_completed":
      return <CriticCard event={event} />;
    case "failure_diagnosed":
      return <FailureCard event={event} />;
    case "skill_promoted":
    case "skill_candidate_created":
      return <SkillCard event={event} />;
    default:
      return <DefaultRow event={event} />;
  }
}

function CardChrome({
  event,
  children,
  size = "md",
}: {
  event: AgentEvent;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg";
}) {
  const accent = accentForEvent(event.event_type);
  const padY = size === "sm" ? "var(--sp-2)" : "var(--sp-3)";
  return (
    <article
      className="card card-accent"
      style={
        {
          padding: `${padY} var(--sp-4)`,
          ["--card-accent-color" as never]: accent,
        } as React.CSSProperties
      }
    >
      <div
        className="row-tight"
        style={{ gap: "var(--sp-2)", marginBottom: 4 }}
      >
        <span
          className="t-label"
          style={{ color: accent }}
        >
          {labelForEvent(event.event_type)}
        </span>
        <div className="spacer" />
        {event.cycle != null && (
          <span className="t-label">cycle {event.cycle}</span>
        )}
        <span className="t-label">{formatTime(event.timestamp)}</span>
      </div>
      {children}
    </article>
  );
}

function GoalCard({ event }: { event: AgentEvent }) {
  const goal = (event.data.task ?? event.data.goal ?? "") as string;
  const rationale = event.data.rationale as string | undefined;
  return (
    <CardChrome event={event} size="lg">
      <div
        style={{
          fontSize: "var(--t-20)",
          fontWeight: 600,
          letterSpacing: "var(--track-20)",
          color: "var(--text)",
          lineHeight: 1.3,
        }}
      >
        {goal || "(empty goal)"}
      </div>
      {rationale && (
        <div
          style={{
            marginTop: 6,
            fontSize: "var(--t-12)",
            color: "var(--text-secondary)",
            lineHeight: 1.5,
          }}
        >
          {rationale}
        </div>
      )}
    </CardChrome>
  );
}

function PlanCard({ event }: { event: AgentEvent }) {
  const explain = event.data.explain as string | undefined;
  const steps = (event.data.steps as string[] | undefined) ?? [];
  const action = event.data.action as { code?: string } | undefined;
  const code =
    (event.data.code as string | undefined) ??
    action?.code ??
    "";
  const [open, setOpen] = useState(true);

  return (
    <CardChrome event={event}>
      {explain && (
        <div
          style={{
            fontSize: "var(--t-14)",
            color: "var(--text)",
            marginBottom: steps.length > 0 || code ? 8 : 0,
            lineHeight: 1.5,
          }}
        >
          {explain}
        </div>
      )}
      {steps.length > 0 && (
        <ol
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 4,
            margin: 0,
            paddingLeft: 0,
            listStyle: "none",
            counterReset: "step",
            fontSize: "var(--t-13, 13px)",
            color: "var(--text-secondary)",
          }}
        >
          {steps.map((s, i) => (
            <li
              key={i}
              style={{
                display: "grid",
                gridTemplateColumns: "20px 1fr",
                gap: "var(--sp-2)",
              }}
            >
              <span
                className="t-mono t-num"
                style={{
                  color: "var(--text-tertiary)",
                  fontSize: "var(--t-11)",
                  paddingTop: 2,
                }}
              >
                {String(i + 1).padStart(2, "0")}
              </span>
              <span>{s}</span>
            </li>
          ))}
        </ol>
      )}
      {code && (
        <details
          open={open}
          onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
          style={{ marginTop: 8 }}
        >
          <summary
            className="t-label"
            style={{
              cursor: "pointer",
              color: "var(--text-tertiary)",
              userSelect: "none",
              listStyle: "none",
            }}
          >
            {open ? "▾ code" : "▸ code"}
          </summary>
          <pre className="code-block" style={{ marginTop: 6 }}>
            {code.slice(0, 2000)}
          </pre>
        </details>
      )}
    </CardChrome>
  );
}

function ActionStartedRow({ event }: { event: AgentEvent }) {
  const exec = event.data.execution as Record<string, unknown> | undefined;
  const name =
    (event.data.name as string | undefined) ??
    (exec?.action_id as string | undefined) ??
    "action";
  return (
    <CardChrome event={event} size="sm">
      <div className="row-tight" style={{ gap: "var(--sp-2)" }}>
        <span aria-hidden style={{ color: "var(--info)" }}>▶</span>
        <span style={{ color: "var(--text)", fontSize: "var(--t-14)" }}>
          {name}
        </span>
      </div>
    </CardChrome>
  );
}

function ActionCompletedRow({ event }: { event: AgentEvent }) {
  const exec = event.data.execution as Record<string, unknown> | undefined;
  const success = exec?.success ?? event.data.success;
  const result = (exec?.result ?? event.data.result ?? "") as string;
  const ms = (event.data.wallMs ?? event.data.durationMs) as number | undefined;
  return (
    <CardChrome event={event} size="sm">
      <div className="row-tight" style={{ gap: "var(--sp-2)" }}>
        <Pill
          tone={success ? "success" : "danger"}
          icon={success ? "✓" : "✗"}
        >
          {success ? "ok" : "fail"}
        </Pill>
        {ms != null && (
          <span className="t-num t-mono" style={{ color: "var(--text-tertiary)", fontSize: "var(--t-12)" }}>
            {ms}ms
          </span>
        )}
        {result && (
          <span
            className="truncate"
            style={{ color: "var(--text-secondary)", fontSize: "var(--t-13, 13px)" }}
            title={result}
          >
            {result}
          </span>
        )}
      </div>
    </CardChrome>
  );
}

function CriticCard({ event }: { event: AgentEvent }) {
  const v = event.data.verdict as Record<string, string> | string | undefined;
  const verdict = typeof v === "string" ? v : v?.verdict ?? "unknown";
  const feedback =
    typeof v === "string" ? "" : (v?.feedback ?? "");
  const tone: PillTone =
    verdict === "success"
      ? "success"
      : verdict === "failed"
        ? "danger"
        : verdict === "incomplete" || verdict === "stuck"
          ? "warning"
          : "neutral";
  return (
    <CardChrome event={event}>
      <div className="row-tight" style={{ gap: "var(--sp-2)", marginBottom: feedback ? 6 : 0 }}>
        <Pill tone={tone} icon={tone === "success" ? "✓" : tone === "danger" ? "✗" : "·"}>
          {verdict}
        </Pill>
      </div>
      {feedback && (
        <details>
          <summary
            className="t-label"
            style={{ cursor: "pointer", listStyle: "none" }}
          >
            ▸ reasoning
          </summary>
          <div
            style={{
              marginTop: 6,
              fontSize: "var(--t-13, 13px)",
              color: "var(--text-secondary)",
              lineHeight: 1.5,
              borderLeft: "2px solid var(--bg-active)",
              paddingLeft: "var(--sp-3)",
            }}
          >
            {feedback}
          </div>
        </details>
      )}
    </CardChrome>
  );
}

function FailureCard({ event }: { event: AgentEvent }) {
  const diag = event.data.diagnosis as Record<string, string> | undefined;
  const cause = diag?.cause ?? (event.data.cause as string) ?? "";
  const failureType = diag?.failure_type ?? "failure";
  return (
    <CardChrome event={event}>
      <div className="row-tight" style={{ gap: "var(--sp-2)", marginBottom: 6 }}>
        <Pill tone="danger" icon="✗">{failureType}</Pill>
      </div>
      {cause && (
        <div style={{ fontSize: "var(--t-14)", color: "var(--text)", lineHeight: 1.5 }}>
          {cause}
        </div>
      )}
    </CardChrome>
  );
}

function SkillCard({ event }: { event: AgentEvent }) {
  const skill = event.data.skill as
    | { name?: string; goal?: string; version?: number }
    | undefined;
  const name = skill?.name ?? (event.data.name as string) ?? "unnamed skill";
  const goal = skill?.goal ?? "";
  const promoted = event.event_type === "skill_promoted";
  return (
    <CardChrome event={event}>
      <div className="row-tight" style={{ gap: "var(--sp-2)" }}>
        <Pill tone={promoted ? "success" : "warning"} icon={promoted ? "★" : "✦"}>
          {promoted ? "promoted" : "candidate"}
        </Pill>
        <span style={{ color: "var(--text)", fontSize: "var(--t-14)", fontWeight: 500 }}>
          {name}
        </span>
        {skill?.version != null && (
          <span className="t-num t-mono" style={{ color: "var(--text-tertiary)", fontSize: "var(--t-12)" }}>
            v{skill.version}
          </span>
        )}
      </div>
      {goal && (
        <div style={{ marginTop: 4, color: "var(--text-secondary)", fontSize: "var(--t-12)" }}>
          {goal}
        </div>
      )}
    </CardChrome>
  );
}

function DefaultRow({ event }: { event: AgentEvent }) {
  // Look for a narration audio clip (event payload may carry audio_url or clipId).
  const clipId =
    (event.data.clip_id as string | undefined) ??
    (event.data.clipId as string | undefined);
  const audioUrl =
    (event.data.audio_url as string | undefined) ??
    (clipId ? narrationUrl(clipId) : undefined);
  const text = (event.data.text as string | undefined) ?? "";
  const isNarration =
    !!text && (audioUrl || event.event_type.includes("narration"));

  if (isNarration) {
    return (
      <CardChrome event={event}>
        <div style={{ fontSize: "var(--t-14)", fontStyle: "italic", color: "var(--text)", marginBottom: 6 }}>
          “{text}”
        </div>
        {audioUrl && (
          <audio
            controls
            src={audioUrl}
            style={{ width: "100%", height: 32 }}
          />
        )}
      </CardChrome>
    );
  }

  const summary = (() => {
    try {
      const s = JSON.stringify(event.data);
      return s === "{}" ? "" : s;
    } catch {
      return "";
    }
  })();

  return (
    <CardChrome event={event} size="sm">
      {summary ? (
        <span
          className="t-mono truncate"
          style={{
            display: "block",
            color: "var(--text-tertiary)",
            fontSize: "var(--t-12)",
          }}
          title={summary}
        >
          {summary.slice(0, 200)}
        </span>
      ) : null}
    </CardChrome>
  );
}
