"use client";

import { StatusBar } from "../components/StatusBar";
import { AgentThoughtStream } from "../components/AgentThoughtStream";
import { PromptInput } from "../components/PromptInput";
import { SkillLibrary } from "../components/SkillLibrary";
import { ExecutionLog } from "../components/ExecutionLog";
import { MetricsRibbon } from "../components/MetricsRibbon";
import { GoalPanel } from "../components/GoalPanel";
import { BotView } from "../components/BotView";
import { NarrationPlayer } from "../components/NarrationPlayer";
import { useEventStream } from "../lib/useEventStream";

export default function HomePage() {
  // Single shared WebSocket connection — every panel reads from it
  // (avoids multiple simultaneous WS connections to the brain).
  const { events, state, reconnect } = useEventStream();

  return (
    <main className="shell">
      <StatusBar connection={state} />
      <MetricsRibbon events={events} />

      <div className="shell__main">
        {/* Left column: goal context + spatial bot view */}
        <div className="shell__left">
          <GoalPanel events={events} />
          <BotView events={events} />
        </div>

        {/* Center column: primary agent thought stream */}
        <AgentThoughtStream
          events={events}
          connection={state}
          onRetry={reconnect}
        />

        {/* Right column: skill library + narration player */}
        <div className="shell__right">
          <SkillLibrary events={events} />
          <NarrationPlayer events={events} />
        </div>
      </div>

      <ExecutionLog events={events} defaultOpen={false} />
      <PromptInput />
    </main>
  );
}
