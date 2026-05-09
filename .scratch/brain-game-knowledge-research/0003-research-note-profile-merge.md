# Merge Research Notes into Game Profiles cautiously

Type: AFK

Label: `ready-for-agent`

## Parent

Local PRD: `docs/prd/brain-game-knowledge-research.md`

## What to build

Extend Game Profile creation so Research Notes can improve incomplete or unknown Game Profiles without overwriting trusted static defaults. The output should remain a structured Game Profile with explicit source and confidence, and the merge behavior should be deterministic enough to test without an LLM or network call.

This slice connects static knowledge and researched knowledge through one small GameProfileBuilder interface.

## Acceptance criteria

- [ ] Research Notes can raise confidence or fill missing fields for an unknown or low-confidence Game Profile.
- [ ] Static Minecraft and Minetest defaults are not overwritten by lower-confidence research notes.
- [ ] Merged profiles preserve source semantics so callers can tell whether the profile is `static`, `researched`, or user-provided.
- [ ] Tests cover research-note merging, static-profile preservation, unknown-game repair, and confidence behavior through the public GameProfileBuilder interface.
- [ ] Merge behavior is deterministic and does not require external API calls.

## Blocked by

- `.scratch/brain-game-knowledge-research/0001-static-game-profiles.md`
- `.scratch/brain-game-knowledge-research/0002-structured-researcher.md`
