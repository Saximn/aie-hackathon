"use client";

import { useMemo, useState } from "react";
import type { AgentEvent } from "../lib/brain";
import { Tabs, EmptyState } from "./ui";
import type { TabItem } from "./ui";

type FilterId = "all" | "errors" | "skills";

const FILTERS: ReadonlyArray<TabItem<FilterId>> = [
  { value: "all", label: "All" },
  { value: "errors", label: "Errors" },
  { value: "skills", label: "Skills" },
];

function formatTime(ts: string | undefined): string {
  if (!ts) return "--:--:--";
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

function verdictOf(evt: AgentEvent): string | null {
  if (evt.event_type !== "verification_completed") return null;
  const v = evt.data.verdict as Record<string, string> | string | undefined;
  if (typeof v === "string") return v;
  return v?.verdict ?? null;
}

function isError(evt: AgentEvent): boolean {
  return (
    evt.event_type === "failure_diagnosed" || verdictOf(evt) === "failed"
  );
}

function isSkillEvent(evt: AgentEvent): boolean {
  return (
    evt.event_type === "skill_promoted" ||
    evt.event_type === "skill_candidate_created"
  );
}

function eventTone(evt: AgentEvent): string {
  if (isError(evt)) return "var(--danger)";
  if (verdictOf(evt) === "success" || evt.event_type === "skill_promoted")
    return "var(--success)";
  if (evt.event_type === "plan_created") return "var(--preview)";
  if (evt.event_type === "goal_received") return "var(--develop)";
  return "var(--text-tertiary)";
}

export interface ExecutionLogProps {
  events: AgentEvent[];
  /** Initial open state (default: collapsed). */
  defaultOpen?: boolean;
}

/**
 * Collapsible drawer with a raw event firehose. Hidden by default so it
 * doesn't dominate the primary panel.
 */
export function ExecutionLog({ events, defaultOpen = false }: ExecutionLogProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [filter, setFilter] = useState<FilterId>("all");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const filtered = useMemo(() => {
    if (filter === "errors") return events.filter(isError);
    if (filter === "skills") return events.filter(isSkillEvent);
    return events;
  }, [events, filter]);

  const tabs: ReadonlyArray<TabItem<FilterId>> = FILTERS.map((f) => ({
    ...f,
    count:
      f.value === "all"
        ? events.length
        : f.value === "errors"
          ? events.filter(isError).length
          : events.filter(isSkillEvent).length,
  }));

  return (
    <section
      className="panel panel-flat"
      role="region"
      aria-label="Execution log"
      style={{ overflow: "hidden" }}
    >
      <header
        className="panel__header"
        style={{ cursor: "pointer", userSelect: "none" }}
        onClick={() => setOpen((o) => !o)}
      >
        <span aria-hidden style={{ color: "var(--text-tertiary)" }}>
          {open ? "▾" : "▸"}
        </span>
        <span className="panel__title">Execution log</span>
        <span
          className="t-label t-num"
          style={{ marginLeft: 6 }}
        >
          {events.length} events
        </span>
        <div className="spacer" />
        {open && (
          <div onClick={(e) => e.stopPropagation()}>
            <Tabs<FilterId>
              items={tabs}
              value={filter}
              onChange={setFilter}
            />
          </div>
        )}
      </header>

      {open && (
        <div
          className="panel__body"
          style={{
            maxHeight: 280,
            overflowY: "auto",
            padding: "var(--sp-2) var(--sp-3)",
          }}
        >
          {filtered.length === 0 ? (
            <EmptyState
              title={`No ${filter === "all" ? "" : filter + " "}events`}
              hint="Events will appear here as the agent loop runs."
            />
          ) : (
            <ul style={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {[...filtered].reverse().map((evt) => {
                const id = evt._localId ?? evt.id ?? `${evt.event_type}-${evt.timestamp}`;
                const isOpen = expanded.has(id);
                return (
                  <li
                    key={id}
                    style={{
                      padding: "4px var(--sp-2)",
                      borderRadius: "var(--radius-sm)",
                      transition: "background var(--d-fast) var(--ease)",
                    }}
                  >
                    <div
                      className="row-tight"
                      style={{ gap: "var(--sp-2)", fontSize: "var(--t-12)" }}
                    >
                      <span
                        className="t-mono"
                        style={{
                          color: "var(--text-tertiary)",
                          fontVariantNumeric: "tabular-nums",
                          minWidth: 60,
                        }}
                      >
                        {formatTime(evt.timestamp)}
                      </span>
                      <span
                        className="t-mono"
                        style={{
                          color: eventTone(evt),
                          fontWeight: 500,
                          textTransform: "uppercase",
                          letterSpacing: "0.04em",
                          fontSize: "var(--t-11)",
                          minWidth: 160,
                        }}
                      >
                        {evt.event_type.replace(/_/g, " ")}
                      </span>
                      {evt.cycle != null && (
                        <span className="t-label">c{evt.cycle}</span>
                      )}
                      <button
                        className="btn btn-ghost btn-sm"
                        style={{ padding: "0 6px" }}
                        onClick={() => {
                          const next = new Set(expanded);
                          next.has(id) ? next.delete(id) : next.add(id);
                          setExpanded(next);
                        }}
                        aria-expanded={isOpen}
                        aria-label="Toggle JSON payload"
                      >
                        {isOpen ? "hide" : "json"}
                      </button>
                    </div>
                    {isOpen && (
                      <pre
                        className="code-block"
                        style={{ marginTop: 4, fontSize: "var(--t-11)" }}
                      >
                        {JSON.stringify(evt.data, null, 2)}
                      </pre>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
