---
name: automation-whats-maintenance
description: Maintain, test, diagnose, document, or operate the Automation Whats repository that integrates Evolution API, Google Sheets, Google Forms, FastAPI, and Docker Compose. Use only for tasks in this repository.
---

# Automation Whats Maintenance

Work from the repository root. Start with `AI_CONTEXT.md` and `git status
--short`, then read only the task-specific document linked there. Preserve
unrelated changes and avoid `venv/`, `.git/`, `__pycache__/`, `.env`, and
`credentials/` during discovery.

## Boundaries

- Treat unit tests as offline: mocks must not send WhatsApp or write Sheets.
- Treat `scripts.send_*`, `scripts.process_*`, webhook configuration, production
  Compose changes, and live POST requests as externally mutating actions.
- Never expose or commit secrets, OAuth tokens, service-account JSON, QR codes,
  dumps, logs with personal data, or real phone numbers.
- The Python app does not own PostgreSQL/Redis; those back Evolution API.
- Production Compose does not run FastAPI. Follow `docs/PRODUCTION.md` or scope
  an infrastructure change explicitly.

## Validation

For Python changes, run the focused test and then:

```powershell
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m unittest discover -v
```

For Compose changes, run `docker compose -f docker-compose.yml -f
docker-compose.<environment>.yml config`. Verify live services only when the
task calls for runtime operation.

Update the relevant document and `AI_CONTEXT.md` whenever commands,
architecture, configuration, validated state, risks, or next steps change.
