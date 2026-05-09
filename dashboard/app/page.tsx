"use client";

import { BotView } from "../components/BotView";
import { GoalPanel } from "../components/GoalPanel";
import { EventFeed } from "../components/EventFeed";
import { SkillLibrary } from "../components/SkillLibrary";
import { NarrationPlayer } from "../components/NarrationPlayer";

export default function HomePage() {
  return (
    <main
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gridTemplateRows: "auto 1fr 1fr auto",
        gridTemplateAreas: `"header header" "view goal" "feed skills" "narrator narrator"`,
        gap: 16,
        padding: 16,
        minHeight: "100vh"
      }}
    >
      <header style={{ gridArea: "header" }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>OmniPlay-MC</h1>
        <p style={{ margin: "4px 0 0", color: "var(--muted)" }}>
          Voyager modernized onto GPT-5.5 — live agent goals, code-as-policy, skill memory, and narration.
        </p>
      </header>
      <section style={{ gridArea: "view" }}>
        <BotView />
      </section>
      <section style={{ gridArea: "goal" }}>
        <GoalPanel />
      </section>
      <section style={{ gridArea: "feed" }}>
        <EventFeed />
      </section>
      <section style={{ gridArea: "skills" }}>
        <SkillLibrary />
      </section>
      <footer style={{ gridArea: "narrator" }}>
        <NarrationPlayer />
      </footer>
    </main>
  );
}
