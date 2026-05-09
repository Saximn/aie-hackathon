"use client";

import { useEffect, useMemo, useState } from "react";
import {
  fetchMetrics,
  type AgentEvent,
  type MetricsResponse,
} from "../lib/brain";
import { Panel, Input, Pill, EmptyState } from "./ui";

export interface SkillEntry {
  name: string;
  goal?: string;
  version?: number;
  /** ISO timestamp of last promotion / draft. */
  lastUsedAt?: string;
  /** Code body when the source had it (renders on expand). */
  code?: string;
  /** Whether the skill was promoted (success) or still candidate. */
  promoted: boolean;
}

export interface SkillLibraryProps {
  /** Live event stream — used to derive skill entries client-side. */
  events?: AgentEvent[];
  /** Test injection: pre-populated skill list. */
  initialSkills?: SkillEntry[] | null;
  /** Test injection: metrics payload (used when no events). */
  initialMetrics?: MetricsResponse | null;
}

function relativeTime(iso?: string): string {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  const diff = Date.now() - t;
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

function deriveSkills(events: AgentEvent[]): SkillEntry[] {
  const map = new Map<string, SkillEntry>();
  for (const e of events) {
    if (
      e.event_type !== "skill_promoted" &&
      e.event_type !== "skill_candidate_created"
    )
      continue;
    const skill = e.data.skill as
      | { name?: string; goal?: string; version?: number; code?: string }
      | undefined;
    const name =
      skill?.name ?? (e.data.name as string | undefined) ?? "unnamed";
    const existing = map.get(name);
    const promoted =
      e.event_type === "skill_promoted" || existing?.promoted || false;
    map.set(name, {
      name,
      goal: skill?.goal ?? existing?.goal,
      version: skill?.version ?? existing?.version,
      lastUsedAt: e.timestamp ?? existing?.lastUsedAt,
      code: skill?.code ?? existing?.code,
      promoted,
    });
  }
  // Sort: promoted first, then by recency.
  return [...map.values()].sort((a, b) => {
    if (a.promoted !== b.promoted) return a.promoted ? -1 : 1;
    return (b.lastUsedAt ?? "").localeCompare(a.lastUsedAt ?? "");
  });
}

export function SkillLibrary({
  events = [],
  initialSkills = null,
  initialMetrics = null,
}: SkillLibraryProps) {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(initialMetrics);
  const [filter, setFilter] = useState("");
  const [openName, setOpenName] = useState<string | null>(null);

  useEffect(() => {
    if (initialMetrics !== null || initialSkills !== null) return;
    let stop = false;
    const poll = async () => {
      try {
        const m = await fetchMetrics();
        if (!stop) setMetrics(m);
      } catch {
        /* fail silently */
      }
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, [initialMetrics, initialSkills]);

  const derived = useMemo(() => {
    if (initialSkills) return initialSkills;
    const fromEvents = deriveSkills(events);
    if (fromEvents.length > 0) return fromEvents;
    // Fallback: synthesize entries from /metrics.recent_skills
    const names = metrics?.recent_skills ?? [];
    return names.map<SkillEntry>((name) => ({
      name,
      promoted: false,
    }));
  }, [events, initialSkills, metrics]);

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return derived;
    return derived.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        (s.goal ?? "").toLowerCase().includes(q),
    );
  }, [derived, filter]);

  const trailing = (
    <span className="t-label t-num">
      {filtered.length} {filtered.length === 1 ? "skill" : "skills"}
    </span>
  );

  return (
    <Panel
      className="panel-skills"
      title="Skill library"
      trailing={trailing}
      toolbar={
        <Input
          placeholder="Filter skills…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          aria-label="Filter skills"
          style={{ height: 32, fontSize: "var(--t-13, 13px)" }}
        />
      }
      flush
    >
      <div
        style={{
          flex: 1,
          minHeight: 0,
          overflow: "auto",
          padding: "var(--sp-3) var(--sp-4)",
        }}
      >
        {filtered.length === 0 ? (
          <EmptyState
            title="No skills yet"
            hint="The agent will populate this as it learns. Send a task to trigger planning."
          />
        ) : (
          <ul style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {filtered.map((s) => {
              const open = openName === s.name;
              return (
                <li key={s.name}>
                  <button
                    onClick={() => setOpenName(open ? null : s.name)}
                    aria-expanded={open}
                    style={{
                      width: "100%",
                      display: "flex",
                      flexDirection: "column",
                      gap: 4,
                      padding: "var(--sp-2) var(--sp-3)",
                      borderRadius: "var(--radius)",
                      background: open ? "var(--bg-active)" : "transparent",
                      transition: "background var(--d-fast) var(--ease)",
                      textAlign: "left",
                    }}
                  >
                    <div className="row-tight" style={{ gap: "var(--sp-2)" }}>
                      <Pill
                        tone={s.promoted ? "success" : "warning"}
                        icon={s.promoted ? "★" : "✦"}
                      >
                        {s.promoted ? "ok" : "draft"}
                      </Pill>
                      <span
                        className="truncate"
                        style={{
                          color: "var(--text)",
                          fontSize: "var(--t-13, 13px)",
                          fontWeight: 500,
                          flex: 1,
                          minWidth: 0,
                        }}
                        title={s.name}
                      >
                        {s.name}
                      </span>
                      <span className="t-label">
                        {relativeTime(s.lastUsedAt)}
                      </span>
                    </div>
                    {s.goal && (
                      <span
                        className="truncate"
                        style={{
                          color: "var(--text-tertiary)",
                          fontSize: "var(--t-12)",
                          paddingLeft: 4,
                        }}
                        title={s.goal}
                      >
                        {s.goal}
                      </span>
                    )}
                  </button>
                  {open && s.code && (
                    <pre className="code-block" style={{ marginTop: 6 }}>
                      {s.code.slice(0, 4000)}
                    </pre>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </Panel>
  );
}
