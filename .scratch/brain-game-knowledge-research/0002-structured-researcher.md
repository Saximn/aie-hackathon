# Add provider-backed Researcher returning structured Research Notes

Type: AFK

Label: `ready-for-agent`

## Parent

Local PRD: `docs/prd/brain-game-knowledge-research.md`

## What to build

Build a Researcher path that accepts a game-knowledge query and returns a structured Research Note. The Researcher should hide provider details behind a small interface, support a fake provider in tests, and keep external retrieval optional through configuration.

This slice does not need real scraping to be useful. It should prove that researched knowledge can enter the Brain as concise, inspectable, structured data.

## Acceptance criteria

- [ ] Researcher returns a Research Note with query, summary, source URLs, and confidence.
- [ ] Researcher can be constructed with a fake provider for tests.
- [ ] Provider failures return a controlled failure or low-confidence note without leaking provider internals.
- [ ] Tests verify behavior through Researcher's public interface and do not call the network.
- [ ] No raw scraped pages are passed into core models.
- [ ] API keys or provider credentials are read only from environment/configuration and are never logged.

## Blocked by

None - can start immediately.
