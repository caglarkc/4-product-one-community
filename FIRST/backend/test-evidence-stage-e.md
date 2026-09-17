# E integration revision — trusted proxy client IP

Task: E gate IP attribution revision; no F account-management endpoints.
Files: `accounts/proxy.py`, `accounts/views.py`, `accounts/tests/test_proxy.py`,
`config/settings.py`, `.env.example`, `README.md`.

Added opt-in HMAC client-IP assertions checked before session access for every
`/api/auth/` path. Missing/invalid configured assertions return 403/no-store;
unsigned mode ignores supplied headers and keeps REMOTE_ADDR. Both current rate
counter call sites use the shared client_ip helper. Secret length is checked at
settings load. IP parsing rejects lists/scopes/whitespace and canonicalizes valid
IPv6 addresses after signature verification. CSRF is unchanged.

Commands from repository root:
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py test accounts --settings=config.test_settings --verbosity 1`
  **35/35 passed**, 0.400 seconds; includes 7 new proxy tests covering distinct IP
  budgets, all-route assertion requirement, spoofed IP/signature, stale/future
  timestamp, method/path substitution, invalid IP/time, IPv6 equivalent budget,
  default-mode spoof ignore, and short secret configuration.
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py makemigrations --check --dry-run --settings=config.test_settings`
  **passed**, no changes detected.
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py check --settings=config.test_settings`
  **passed**, no issues (0 silenced).

No failed backend checks occurred in this revision. The integration finding that
triggered it is preserved in the parent E graph/evidence, not marked as initially
passed here. Independent integration re-review is parent-managed and pending.

Not verified: trusted ingress actually overwrites the configured frontend header,
real deployed clocks/key agreement, browser/Next transport, Redis production
atomicity or PostgreSQL behavior. Tests use in-process Django clients, FakeRedis,
SQLite and no listening services. Signed assertions are replayable inside their
60-second freshness window; transport confidentiality is a deployment requirement.
