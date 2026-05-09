# Add AgentLoop research decision tracer bullet

Type: AFK

Label: `ready-for-agent`

## Parent

Local PRD: `docs/prd/brain-game-knowledge-research.md`

## What to build

Add a narrow AgentLoop tracer bullet that demonstrates when the Brain uses known Game Profile knowledge and when it asks the Researcher for missing knowledge. The slice should use fake subcomponents in tests so it does not depend on the runtime bot, OpenAI, or external retrieval.

The goal is not full autonomous gameplay. The goal is an observable orchestration path: profile, optional research, memory context, planning boundary, validation, verification/diagnosis/recovery decision, and Agent Events for research start/completion.

## Acceptance criteria

- [ ] For a known high-confidence game profile, AgentLoop does not call Researcher before planning.
- [ ] For an unknown or incomplete profile, AgentLoop calls Researcher and uses the resulting Research Note before planning.
- [ ] For a repeated missing-strategy diagnosis, AgentLoop follows a research transition instead of blindly replanning.
- [ ] AgentLoop emits Agent Events for research start and research completion.
- [ ] Tests use fake subcomponents and verify observable transitions through AgentLoop's public interface.
- [ ] No real runtime bot, LLM, scraping, or external API call is required.

## Blocked by

- `.scratch/brain-game-knowledge-research/0001-static-game-profiles.md`
- `.scratch/brain-game-knowledge-research/0002-structured-researcher.md`
- `.scratch/brain-game-knowledge-research/0003-research-note-profile-merge.md`
