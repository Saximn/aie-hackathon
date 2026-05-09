# Persist useful Research Notes and profile updates in memory

Type: AFK

Label: `ready-for-agent`

## Parent

Local PRD: `docs/prd/brain-game-knowledge-research.md`

## What to build

Make useful game knowledge durable by persisting Research Notes and profile updates through MemoryStore after the AgentLoop decides they matter. Future Brain cycles should be able to retrieve relevant game knowledge without repeating external research.

This slice should preserve the core design rule: memory is a persistence boundary, not a place where planning, scraping, or diagnosis logic leaks.

## Acceptance criteria

- [ ] Research Notes that affect behavior can be persisted through MemoryStore.
- [ ] Profile updates or repaired profile context can be persisted without exposing provider-specific types.
- [ ] Memory retrieval can return game-knowledge context separately enough that Planner input does not confuse game rules with episodic failures.
- [ ] Tests use fake memory clients and do not call external services.
- [ ] Secrets and API keys are never logged or committed.
- [ ] Existing memory-store behavior remains covered by tests.

## Blocked by

- `.scratch/brain-game-knowledge-research/0003-research-note-profile-merge.md`
- `.scratch/brain-game-knowledge-research/0004-agentloop-research-decision.md`
