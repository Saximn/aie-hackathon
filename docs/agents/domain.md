# Domain Docs

This is a single-context repo. Engineering skills should use the root `CONTEXT.md` as the source of domain language, architecture, module boundaries, contracts, and current implementation constraints.

## Before Exploring

Read these files when they are relevant to the task:

- `CONTEXT.md` at the repo root
- `docs/adr/` for architectural decisions that touch the area being changed

If an ADR directory or relevant ADR does not exist yet, proceed silently. Do not block work just because a decision has not been recorded.

## Single-Context Layout

Expected layout:

```text
/
  CONTEXT.md
  docs/
    adr/
    agents/
```

Do not create `CONTEXT-MAP.md` unless this repo grows separate domain contexts that need their own context files.

## Vocabulary

When naming domain concepts in issue titles, hypotheses, tests, refactor plans, or code comments, use the terms from `CONTEXT.md`.

If a concept is missing from `CONTEXT.md`, either reconsider whether the term belongs in this project or note the gap for a later documentation pass.

## ADR Conflicts

If a recommendation or code change contradicts an existing ADR, surface that explicitly and explain why the decision should be revisited.
