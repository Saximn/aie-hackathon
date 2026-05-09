"use client";

import { useState } from "react";

const BRAIN_URL = process.env.NEXT_PUBLIC_BRAIN_URL ?? "http://localhost:8000";

type SendState = "idle" | "sending" | "sent" | "error";

export function PromptInput() {
  const [task, setTask] = useState("");
  const [state, setState] = useState<SendState>("idle");
  const [message, setMessage] = useState<string | null>(null);

  const canSubmit = task.trim().length > 0 && state !== "sending";

  const submit = async () => {
    if (!canSubmit) return;
    setState("sending");
    try {
      const res = await fetch(`${BRAIN_URL}/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: task.trim() }),
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => ({}))) as {
          detail?: string;
        };
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      const data = (await res.json()) as { queued_position: number };
      setState("sent");
      setMessage(`Queued at position ${data.queued_position}`);
      setTask("");
      setTimeout(() => {
        setState("idle");
        setMessage(null);
      }, 3500);
    } catch (e) {
      setState("error");
      setMessage(
        e instanceof Error ? e.message : "Failed to reach brain API"
      );
      setTimeout(() => {
        setState("idle");
        setMessage(null);
      }, 5000);
    }
  };

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
  };

  return (
    <div
      style={{
        background: "var(--panel)",
        boxShadow: "rgba(0,0,0,0.5) 0px 0px 0px 1px",
        borderRadius: 12,
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
        }}
      >
        <span style={{ fontSize: 13, fontWeight: 600, letterSpacing: "-0.2px" }}>
          Send task to agent
        </span>
        <span
          style={{
            fontSize: 10,
            color: "var(--muted)",
            fontFamily: "var(--font-mono)",
          }}
        >
          POST /prompt · ⌘↵
        </span>
      </div>

      {/* Input row */}
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={handleKey}
          placeholder="e.g. build a dirt house near spawn…"
          disabled={state === "sending"}
          style={{
            flex: 1,
            background: "var(--code-bg)",
            border: "none",
            boxShadow: "rgba(0,0,0,0.5) 0px 0px 0px 1px",
            borderRadius: 6,
            padding: "7px 10px",
            color: "var(--text)",
            fontSize: 13,
            outline: "none",
            fontFamily: "inherit",
            transition: "box-shadow 0.15s",
          }}
          onFocus={(e) => {
            e.currentTarget.style.boxShadow =
              "hsla(212, 100%, 48%, 0.5) 0px 0px 0px 2px";
          }}
          onBlur={(e) => {
            e.currentTarget.style.boxShadow = "rgba(0,0,0,0.5) 0px 0px 0px 1px";
          }}
        />
        <button
          onClick={submit}
          disabled={!canSubmit}
          style={{
            padding: "7px 14px",
            borderRadius: 6,
            border: "none",
            background: !canSubmit
              ? "rgba(154,163,173,0.12)"
              : "var(--accent)",
            color: !canSubmit ? "var(--muted)" : "#fff",
            cursor: !canSubmit ? "not-allowed" : "pointer",
            fontWeight: 600,
            fontSize: 13,
            transition: "background 0.15s, opacity 0.15s",
            whiteSpace: "nowrap",
          }}
        >
          {state === "sending" ? "Sending…" : "Send Task"}
        </button>
      </div>

      {/* Feedback message */}
      {message && (
        <div
          style={{
            fontSize: 12,
            padding: "5px 10px",
            borderRadius: 6,
            background:
              state === "error"
                ? "rgba(240,100,100,0.12)"
                : "rgba(79,209,138,0.12)",
            color: state === "error" ? "var(--danger)" : "var(--success)",
            boxShadow:
              state === "error"
                ? "rgba(240,100,100,0.3) 0px 0px 0px 1px"
                : "rgba(79,209,138,0.3) 0px 0px 0px 1px",
          }}
        >
          {state === "error" ? "✗ " : "✓ "}
          {message}
        </div>
      )}

      {/* Hint */}
      <div
        style={{
          fontSize: 11,
          color: "var(--muted)",
          marginTop: "auto",
          paddingTop: 4,
          lineHeight: 1.5,
        }}
      >
        Tasks are queued and executed by the agent loop in{" "}
        <code
          style={{
            fontFamily: "var(--font-mono)",
            background: "var(--code-bg)",
            padding: "1px 4px",
            borderRadius: 3,
            fontSize: 10,
          }}
        >
          --interactive
        </code>{" "}
        mode.
      </div>
    </div>
  );
}
