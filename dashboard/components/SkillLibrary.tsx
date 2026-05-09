"use client";

import { useState } from "react";
import { useQuery } from "convex/react";
import { api } from "../lib/convex_api";
import { Panel } from "./Panel";

export function SkillLibrary() {
  const skills = useQuery(api.skills.list, { episodeId: null, limit: 100 });
  const [openName, setOpenName] = useState<string | null>(null);

  if (!skills) {
    return (
      <Panel title="Skill library" subtitle="loading…">
        <div style={{ color: "var(--muted)" }}>connecting…</div>
      </Panel>
    );
  }
  return (
    <Panel title="Skill library" subtitle={`${skills.length} skill${skills.length === 1 ? "" : "s"} learned`}>
      {skills.length === 0 ? (
        <div style={{ color: "var(--muted)" }}>No skills yet. Run the agent to learn one.</div>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {(skills as Array<{ _id: string; name: string; goal: string; version: number; code: string }>).map((skill) => {
            const isOpen = openName === skill.name;
            return (
              <li
                key={skill._id}
                style={{
                  padding: "8px 0",
                  borderBottom: "1px solid var(--panel-border)"
                }}
              >
                <button
                  onClick={() => setOpenName(isOpen ? null : skill.name)}
                  style={{
                    width: "100%",
                    background: "transparent",
                    border: "none",
                    color: "var(--text)",
                    cursor: "pointer",
                    textAlign: "left",
                    padding: 0,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline"
                  }}
                >
                  <span style={{ fontWeight: 600 }}>{skill.name}</span>
                  <span style={{ color: "var(--muted)", fontSize: 12 }}>
                    v{skill.version}
                  </span>
                </button>
                <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 2 }}>{skill.goal}</div>
                {isOpen ? (
                  <pre
                    style={{
                      background: "var(--code-bg)",
                      padding: 10,
                      borderRadius: 6,
                      marginTop: 8,
                      maxHeight: 240,
                      overflow: "auto",
                      border: "1px solid var(--panel-border)",
                      fontSize: 11.5
                    }}
                  >
                    {skill.code}
                  </pre>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </Panel>
  );
}
