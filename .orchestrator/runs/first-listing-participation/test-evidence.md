# Test evidence — FIRST listing participation

User explicitly authorized backend → frontend → tests, GitHub delivery, remote deployment and live site checks. Tests here use isolated SQLite/FakeRedis/mocked GitHub, not production identities or external repository writes.

## Backend

- Initial historical suite: 153 tests, 149 failures and 2 errors, dominated by obsolete cookie session/HMAC proxy assumptions. No production authentication change made to satisfy those expectations.
- Test-only BearerClient now follows X-First-Session rotation and sends Authorization: Bearer. Expiry/revocation/CSRF/identity assertions retained using current SessionRecord and header semantics. Trusted nginx/CORS tests replace removed HMAC proxy behavior.
- Existing project tests updated to persisted-preview/taxonomy contracts and database-only ordinary reads.
- 24 new participation integration tests cover authorization, visibility, single active repo/immutable mode, applicant state transitions, durable partial failures, UID pinning, reviewed SHA, selected invitations, notifications and rate limits.
- 21 provider tests cover safe rulesets, all existing branches/tags, private plan support, stable numeric identity, caller-token private reads/public anonymous reads, Issue/PR reconciliation, permission mismatches and bounded HTTP handling.
- Final combined command: `.venv/bin/python manage.py test accounts projects --settings=config.test_settings` → **202 tests passed**; Django system checks clean.
- `.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.test_settings` → **No changes detected**.
- Additional targeted OAuth return-destination injection regression passed.
- Deployment payload dry-run includes all new project modules and migration0004; excludes tests, local dependencies and raw env.

## Boundaries

SQLite tests do not establish PostgreSQL lock scheduling under concurrent processes. Mocked GitHub responses do not prove real merges/invitations. Live release health and site verification are recorded separately in delivery.md after deployment. No real GitHub PR merge, collaborator invite or Issue mutation is used as a test against user repositories without a designated fixture.

## Frontend

- Initial historical suite: 85 failed / 30 passed, including old proxy/cookie assumptions, missing API-origin fixture and components without their SessionProvider boundary.
- Shared test environment supplies a fixed fake HTTPS API origin; transport tests exercise the real direct API, Headers and Bearer storage. Account/logout integration uses the real SessionProvider. Isolated form tests explicitly mock only unrelated route gates. No tests skipped.
- New participation coverage verifies durable failure/retry, reviewed SHA, private access error, recipient-only invitation links, filters/page reset and notification read state.
- Final `npm test`: **123/123 tests passed, 12/12 files**.
- `npm run typecheck`: passed. Stale generated `.next` validators for removed proxy routes were moved to `/tmp`; no production build performed locally.
- `npm run lint`: 0 errors, 1 pre-existing `react-hooks/exhaustive-deps` ref-cleanup warning in session-provider.tsx.
- Independent incremental source/test review accepted transport fixture modernization and frontend reset/identity handling without blocking findings.
- Final `git diff --check`: passed.
