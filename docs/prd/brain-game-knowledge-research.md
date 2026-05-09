# PRD: Brain Game Knowledge And Research

Issue label: `ready-for-agent`

## Problem Statement

OmniForge needs the AI Brain to understand enough about the target game before planning, but the current Brain does not yet build usable game knowledge. The project has contracts for Game Profile creation and Researcher-backed knowledge retrieval, but they are still scaffold-only.

From the user's perspective, this means the Brain cannot yet answer a basic operational question: "Does the Brain know the game before it acts?" For the Minecraft/Minetest demo, the Brain should start from a deterministic Game Profile, use memory where available, and only call external research when the AgentLoop decides knowledge is missing, repeated failures indicate a strategy gap, or the user explicitly asks for coaching.

## Solution

Implement a game-knowledge path for the AI Brain that gives the Planner structured, reliable game context before it creates a Plan.

The solution should start with a deterministic Minecraft/Minetest Game Profile so the demo can run without scraping. Then add a controlled Researcher path that returns structured Research Notes for unknown games, incomplete profiles, repeated failures, missing strategy, or explicit user instruction. The AgentLoop remains responsible for deciding when research is allowed; the Diagnoser can recommend research, but it must not call external retrieval directly.

The result should be a small set of deep modules with simple public interfaces:

- Game Profile creation hides static defaults, research-note merging, confidence rules, and fallback behavior.
- Research hides retrieval provider details and returns structured Research Notes.
- AgentLoop orchestration hides when to use static profile knowledge, memory, research, planning, validation, verification, diagnosis, recovery, and skill creation.
- MemoryStore persists useful Game Profile, Research Note, failure, and Skill context without leaking secrets or provider-specific details into core logic.

## User Stories

1. As a developer, I want the Brain to load a Minecraft Game Profile before planning, so that the first demo has game-specific controls and survival objectives.
2. As a developer, I want the Brain to load a Minetest Game Profile before planning, so that the first benchmark has a second open-world target.
3. As a developer, I want the Game Profile to include controls, core mechanics, early objectives, risks, and adapter hints, so that Planner input is structured instead of free text.
4. As a developer, I want the Game Profile to avoid hardcoded assumptions outside the profile boundary, so that future games can be added without rewriting planning code.
5. As a developer, I want profile confidence to be explicit, so that the AgentLoop can decide whether research is needed.
6. As a developer, I want unknown games to return a low-confidence researched or partial profile, so that the Brain can degrade gracefully.
7. As a developer, I want Researcher to return structured Research Notes, so that researched knowledge can be consumed safely by other modules.
8. As a developer, I want Researcher to include source URLs in Research Notes, so that researched claims are inspectable.
9. As a developer, I want Researcher to avoid returning raw scraped pages, so that Planner receives concise game strategy context.
10. As a developer, I want the AgentLoop to decide when research happens, so that Diagnoser and Planner do not perform uncontrolled external calls.
11. As a developer, I want repeated missing-strategy diagnoses to trigger research, so that the Brain can recover from genuine knowledge gaps.
12. As a developer, I want explicit user coaching to trigger research when useful, so that the Brain can answer "how do I craft X?" style gaps.
13. As a developer, I want the Brain to avoid researching every loop, so that planning remains fast, cheap, and predictable.
14. As a developer, I want researched notes to merge into Game Profiles cautiously, so that unreliable research does not overwrite deterministic defaults.
15. As a developer, I want profile creation to be testable without external network calls, so that CI can validate the behavior.
16. As a developer, I want Researcher to have a fake provider in tests, so that retrieval behavior can be tested through the public interface.
17. As a developer, I want the Planner to receive memory context and profile context separately, so that game rules do not get confused with episodic failures.
18. As a developer, I want the MemoryStore to persist useful Research Notes, so that repeated questions do not need repeated external retrieval.
19. As a developer, I want the MemoryStore to persist useful Game Profile updates, so that improved profiles survive across runs.
20. As a developer, I want the SkillBuilder to use successful plans and researched guidance, so that repeated game knowledge can become reusable Skills.
21. As a developer, I want Skills to remain structured procedures, so that they do not become hidden executable scripts.
22. As a developer, I want the AgentLoop to emit Agent Events for research start and completion, so that the dashboard can explain why the Brain paused to learn.
23. As a developer, I want failed research to produce a clear recovery transition, so that the Brain does not crash when retrieval is unavailable.
24. As a developer, I want secrets and API keys to stay in environment variables only, so that retrieval integration does not leak credentials.
25. As a developer, I want research provider configuration to be optional, so that local deterministic demo behavior still works without external services.
26. As a hackathon judge, I want to see the Brain explain what it knows about Minecraft survival, so that the demo feels grounded.
27. As a hackathon judge, I want to see research happen only when needed, so that the agent looks deliberate rather than noisy.
28. As a user coaching the Brain, I want my instruction to influence future plans, so that the Brain adapts to corrections.
29. As a user coaching the Brain, I want the Brain to remember a useful correction, so that I do not need to repeat it every cycle.
30. As a future contributor, I want a clear extension point for new games, so that adding another open-world game does not require touching every module.

## Implementation Decisions

- Implement static Game Profiles first for Minecraft and Minetest.
- Keep Game Profile creation behind one small public method that accepts a game name and optional Research Notes.
- Treat static profiles as the highest-trust baseline for the demo.
- Add confidence scoring to profile output and preserve the profile source.
- Add deterministic merging from Research Notes into low-confidence or incomplete profiles.
- Implement Researcher as a provider-backed deep module that returns a structured Research Note, not raw provider responses.
- Keep external retrieval optional and configuration-driven.
- AgentLoop owns research orchestration. Research is allowed for unknown games, incomplete profiles, repeated missing-strategy failures, unknown mechanics, or explicit user coaching.
- Diagnoser may set `should_research`, but it does not call Researcher.
- Planner receives a Game Profile, World Snapshot, memory context, and user constraints. It should not scrape or fetch external knowledge directly.
- Research Notes that affect future behavior should be persisted through MemoryStore.
- Agent Events should be emitted for research start and research completion.
- If retrieval fails, the Brain should continue with deterministic profile knowledge when possible or replan/abort with a clear Diagnosis and Recovery Transition.
- Avoid provider-specific types in core models. Provider details stay inside Researcher.
- Do not commit secrets. API keys must remain in environment files or runtime environment variables.

## Testing Decisions

- Tests should verify external behavior through public module interfaces, not private helpers or provider internals.
- Game Profile tests should cover known Minecraft and Minetest profile creation, unknown-game fallback, confidence/source fields, and research-note merging.
- Researcher tests should use a fake retrieval provider and assert that a query becomes a structured Research Note with summary, source URLs, and confidence.
- AgentLoop tests should use fake subcomponents and verify transitions: static profile path, research-needed path, research-failure path, and memory-persisted research path.
- MemoryStore tests should continue to use fake clients and avoid real network calls.
- Planner tests are out of scope until OpenAI Responses API integration is implemented, but Planner inputs should be shaped so they are easy to test later.
- Existing decision-core tests are prior art for deterministic behavior tests in this repo.
- Test names should use domain vocabulary from CONTEXT.md: Game Profile, Research Note, AgentLoop, Planner, World Snapshot, Diagnosis, Recovery Transition, Skill.

## Out of Scope

- Full web scraping infrastructure.
- Autonomous browsing without an explicit Researcher call.
- Replacing deterministic static Game Profiles with research-only profiles.
- Real GPT-5.5 Planner implementation.
- Full AgentLoop autonomous gameplay across many cycles.
- Dashboard UI work.
- Runtime keyboard/mouse implementation.
- Multiplayer, PvP, fast combat, precision platforming, and broad "plays all games" claims.
- Convex schema design beyond the MemoryStore calls needed to persist relevant research/profile context.

## Further Notes

This PRD intentionally keeps research behind the AgentLoop decision boundary. OmniForge should not scrape first on every run. It should know Minecraft/Minetest through deterministic profiles, then research only when knowledge is missing or stale.

The immediate implementation sequence should be:

1. Static GameProfileBuilder for Minecraft/Minetest.
2. Researcher interface with fake-provider tests and optional external provider configuration.
3. Research-note merge behavior into Game Profiles.
4. AgentLoop research decision path.
5. Memory persistence for useful Research Notes and profile updates.
