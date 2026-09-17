# SMTP admission fix evidence

Implementation owner: `/root/review_backend`. Independent review/verify owner: `/root/security_verify`.

Original reproduction: eight rapid email-change requests with distinct destination addresses returned eight 200 responses; 17 memory-backend messages included the initial registration mail. No real mail was sent.

The fix adds one Redis Lua admission operation for stable account ID (60-second interval, five requests/hour) and client IP (30 requests/15 minutes), before destination admission, token issuance and SMTP. The existing destination budget remains. Reservations are retained on downstream failure.

Changed files: accounts/security.py, accounts/account_views.py, accounts/tests/fakes.py, accounts/tests/test_account.py under FIRST/backend.

Implementer executed `.venv/bin/python manage.py test accounts.tests --settings=config.test_settings --verbosity=1`: 69 tests passed. `git diff --check` passed.

Independent security_verify executed `.venv/bin/python manage.py test accounts --settings=config.test_settings`: 69 tests passed. Independent read-only source review found no blocking issue; account/IP atomic admission, ordering and Redis-failure behavior were inspected. Actual Redis concurrency and TTL were not executed. Recommended follow-up: record new admission limits in API documentation.

New regressions cover varied destinations, per-account hourly notification budget, per-IP denial without partial reservation, and fail-closed Redis failure without token/mail. Existing superseded-email-token test now advances the account interval.

All tests used process-local clients, SQLite, fake Redis and memory email. No local server, deployment or live SMTP was performed by these agents.
