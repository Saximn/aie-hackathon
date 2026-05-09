## Working agreements

- Activate the virtual environment before running project commands:
  `. .\.venv\Scripts\Activate.ps1`
- Run tests that cover the modified area before finalizing changes.
- Add or update tests when changing behavior or fixing bugs.
- Do not remove tests unless they are obsolete and the reason is clear.
- If full test execution is expensive, run the smallest meaningful subset and state what was run.

## Security considerations

- Never commit secrets, API keys, tokens, or credentials.
- Do not log sensitive information.
- Treat environment variables and secret files with care.
- Validate external input and avoid unsafe execution patterns.
- Prefer least-privilege access for integrations and services.
- If a task involves authentication, permissions, payments, personal data, or production infrastructure, be extra cautious and explicitly mention any risks.

## OpenAI documentation

Always use the OpenAI developer documentation MCP server when working with the OpenAI API, ChatGPT Apps SDK, Codex, or related OpenAI products.

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `Saximn/aie-hackathon`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-label triage vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo with root `CONTEXT.md` and optional root `docs/adr/` decisions. See `docs/agents/domain.md`.
