# Add static Minecraft and Minetest Game Profiles

Type: AFK

Label: `ready-for-agent`

## Parent

Local PRD: `docs/prd/brain-game-knowledge-research.md`

## What to build

Build the first complete Game Profile path for known demo games. The Brain should be able to ask for Minecraft or Minetest and receive a structured Game Profile with controls, core mechanics, early objectives, benchmark goals, adapter hints, source, and confidence. Unknown games should return a low-confidence fallback profile instead of crashing.

This slice makes the Brain know the demo games before planning without scraping or calling external research.

## Acceptance criteria

- [ ] Building a Minecraft Game Profile returns controls, core mechanics, early-game objectives, the `survive_first_night` benchmark goal, adapter hints, `static` source, and high confidence.
- [ ] Building a Minetest Game Profile returns equivalent structured fields appropriate for the first benchmark.
- [ ] Building an unknown game returns a valid low-confidence Game Profile with the requested game name and no external calls.
- [ ] Tests cover known profiles, unknown fallback, confidence, source, and key domain fields through the public GameProfileBuilder interface.
- [ ] No secrets, network calls, scraping, or provider-specific types are introduced.

## Blocked by

None - can start immediately.
