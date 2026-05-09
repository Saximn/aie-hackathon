"use client";

import { useEffect, useRef, useState } from "react";
import { postPrompt } from "../lib/brain";
import { Button, Input, Kbd } from "./ui";

const EXAMPLES: ReadonlyArray<{ label: string; task: string }> = [
  { label: "Chop a tree", task: "chop a tree" },
  { label: "Build a dirt house", task: "build a dirt house near spawn" },
  { label: "Explore for 30s", task: "explore the area for 30 seconds" },
  { label: "Mine 5 stone", task: "mine 5 stone blocks" },
  { label: "Find water", task: "find the nearest water source" },
];

type SendState = "idle" | "sending" | "sent" | "error";

export interface PromptInputProps {
  /** Override the network call — used by tests. */
  onSubmit?: (task: string) => Promise<{ queued_position: number }>;
}

export function PromptInput({ onSubmit }: PromptInputProps = {}) {
  const [task, setTask] = useState("");
  const [state, setState] = useState<SendState>("idle");
  const [toast, setToast] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [showExamples, setShowExamples] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const examplesRef = useRef<HTMLDivElement>(null);

  const canSubmit = task.trim().length > 0 && state !== "sending";

  // Close examples on outside click
  useEffect(() => {
    if (!showExamples) return;
    const onDoc = (e: MouseEvent) => {
      if (examplesRef.current && !examplesRef.current.contains(e.target as Node)) {
        setShowExamples(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [showExamples]);

  // Auto-dismiss toasts
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(id);
  }, [toast]);

  const submit = async () => {
    if (!canSubmit) return;
    setState("sending");
    try {
      const submitFn = onSubmit ?? postPrompt;
      const data = await submitFn(task.trim());
      setState("sent");
      setToast({
        kind: "success",
        text: `Queued · position ${data.queued_position}`,
      });
      setTask("");
      setTimeout(() => setState("idle"), 800);
    } catch (e) {
      setState("error");
      setToast({
        kind: "error",
        text: e instanceof Error ? e.message : "Failed to reach brain API",
      });
      setTimeout(() => setState("idle"), 1200);
    }
  };

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <>
      <div
        className="panel panel-flat"
        role="form"
        aria-label="Send task to agent"
        style={{
          flexDirection: "row",
          alignItems: "center",
          gap: "var(--sp-3)",
          padding: "var(--sp-3) var(--sp-4)",
          position: "relative",
        }}
      >
        <span className="t-label" style={{ flexShrink: 0 }}>
          task
        </span>

        <Input
          ref={inputRef}
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={onKey}
          placeholder="Tell the agent what to do…"
          disabled={state === "sending"}
          aria-label="Task description"
          style={{ flex: 1, height: 36 }}
        />

        {/* Examples dropdown */}
        <div ref={examplesRef} style={{ position: "relative" }}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowExamples((s) => !s)}
            aria-expanded={showExamples}
            aria-haspopup="menu"
          >
            Examples ▾
          </Button>
          {showExamples && (
            <div
              role="menu"
              style={{
                position: "absolute",
                bottom: "calc(100% + 8px)",
                right: 0,
                minWidth: 220,
                background: "var(--bg-overlay)",
                borderRadius: "var(--radius-md)",
                boxShadow: "var(--shadow-popover)",
                padding: "var(--sp-1)",
                zIndex: 10,
              }}
            >
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  role="menuitem"
                  className="btn btn-ghost"
                  style={{
                    width: "100%",
                    justifyContent: "flex-start",
                    height: 32,
                  }}
                  onClick={() => {
                    setTask(ex.task);
                    setShowExamples(false);
                    inputRef.current?.focus();
                  }}
                >
                  {ex.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <Button
          variant="primary"
          onClick={submit}
          disabled={!canSubmit}
          kbd={
            <>
              <span aria-hidden>⌘</span>
              <span aria-hidden>↵</span>
            </>
          }
          aria-label="Send task to agent (Cmd+Enter)"
        >
          {state === "sending" ? "Sending…" : "Send Task"}
        </Button>
      </div>

      {/* Toast — fixed below the dock */}
      {toast && (
        <div
          className="toast"
          role="status"
          style={{
            color: toast.kind === "success" ? "var(--success)" : "var(--danger)",
            boxShadow: `${toast.kind === "success" ? "rgba(74,222,128,0.4)" : "rgba(255,91,79,0.4)"} 0 0 0 1px, rgba(0,0,0,0.6) 0 8px 32px -4px`,
          }}
        >
          <span aria-hidden>{toast.kind === "success" ? "✓" : "✗"}</span>
          <span>{toast.text}</span>
        </div>
      )}
    </>
  );
}
