"use client";

import { StatusBar } from "../components/StatusBar";
import { AgentThoughtStream } from "../components/AgentThoughtStream";
import { PromptInput } from "../components/PromptInput";
import { ExecutionLog } from "../components/ExecutionLog";
import { SkillLibrary } from "../components/SkillLibrary";
import { BotView } from "../components/BotView";
import { GoalPanel } from "../components/GoalPanel";
import { NarrationPlayer } from "../components/NarrationPlayer";

export default function HomePage() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        padding: 12,
        minHeight: "100vh",
        maxWidth: 1600,
        margin: "0 auto",
      }}
    >
      {/* ── Status bar ───────────────────────────────────────────── */}
      <StatusBar />

      {/* ── Main 3-column grid ──────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "260px 1fr 300px",
          gridTemplateRows: "1fr 1fr",
          gap: 12,
          flex: 1,
          minHeight: 0,
          height: "calc(100vh - 200px)",
        }}
      >
        {/* Left col — BotView + GoalPanel */}
        <div
          style={{
            gridColumn: "1",
            gridRow: "1 / 3",
            display: "flex",
            flexDirection: "column",
            gap: 12,
            minHeight: 0,
          }}
        >
          <div style={{ flex: "0 0 260px" }}>
            <BotView />
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
            <GoalPanel />
          </div>
        </div>

        {/* Center — Agent Thought Stream (spans both rows) */}
        <div
          style={{
            gridColumn: "2",
            gridRow: "1 / 3",
            minHeight: 0,
          }}
        >
          <AgentThoughtStream />
        </div>

        {/* Right col — SkillLibrary top, ExecutionLog bottom */}
        <div
          style={{
            gridColumn: "3",
            gridRow: "1",
            minHeight: 0,
          }}
        >
          <SkillLibrary />
        </div>
        <div
          style={{
            gridColumn: "3",
            gridRow: "2",
            minHeight: 0,
          }}
        >
          <ExecutionLog />
        </div>
      </div>

      {/* ── Bottom row — Prompt + Narration ─────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 12,
          flexShrink: 0,
        }}
      >
        <PromptInput />
        <NarrationPlayer />
      </div>
    </div>
  );
}
