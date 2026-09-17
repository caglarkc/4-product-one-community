# B/C — backend login/register evidence

Owner: backend_writer. Files: `accounts/**`, `config/**`, `requirements.txt`,
`.env.example`, `compose.yaml`, `README.md`. This record preserves unsuccessful
attempts and corrections; no live services were started.

1. `python3 -m venv FIRST/backend/.venv` succeeded. Initial sandboxed
   `.venv/bin/pip install -r requirements.txt 'redis>=5,<7' 'psycopg[binary]>=3.2,<4'`
   failed because DNS/network was unavailable. The authorized escalated retry
   succeeded: Django 5.2.17, DRF 3.18.1, redis 6.4.0, psycopg 3.3.5, gunicorn 26.2.0.
2. `.venv/bin/python manage.py makemigrations accounts --settings=config.test_settings`
   succeeded, generating initial user/session migration. A subsequent migration
   added database case-insensitive email uniqueness.
3. First `.venv/bin/python manage.py test accounts --settings=config.test_settings --verbosity 1`
   ran 19 tests, **failed** with 1 error in register→me: DRF's anonymous default
   authentication replaced middleware user. Added explicit Django session
   authentication; retained explicit anonymous CSRF enforcement.
4. Same command rerun: **19/19 passed**, 0.272 seconds. Added password proof
   admission locking/reservations, absolute expiry, email constraint, session
   rotation and targeted regressions. Expanded run: **24/24 passed**, 0.384 seconds.
5. Added configurable offline breach corpus validation and tests. Final same
   command: **26/26 passed**, 0.370 seconds; system check no issues.
6. `.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.test_settings`:
   **passed**, no changes detected.
7. `.venv/bin/python manage.py check --settings=config.test_settings`: **passed**,
   no issues (0 silenced).

Tests exercise valid register/login/logout/me, memory SMTP content and configured
origin links, 13-year boundary, required fields, case-insensitive uniqueness,
8/20 password boundaries and each character class, Unicode, phone normalization,
unknown writable field rejection, anonymous CSRF with enforcement enabled,
wrong token and cross-origin rejection, generic credential failures, account/IP
limits, in-flight proof admission, cookie flags, remembered lifetime, absolute
registry expiry, replay of revoked sessions, security-version revocation, no-store
headers, response allowlist, SMTP rollback and Redis fail-closed behavior.

Not verified: actual PostgreSQL constraints/row locks and concurrent transactions;
real Redis Lua atomicity, TTL scheduling and network recovery; actual SMTP
submission/delivery; browser proxy/cookie end-to-end behavior; Docker/container
startup, production migration or deploy; completeness/currentness of an external
breach corpus (none supplied). Test double behavior is not evidence of real Redis.
All tests run in-process with isolated SQLite, FakeRedis and locmem email.

Independent review and verification: pending parent-managed separate agents. This
writer record does not claim independent acceptance. Stage F endpoints and email
verification consumption are intentionally absent until the ordered gate passes.

## C independent review revision — NFC username bounds

Independent C review **failed** on a P2 username normalization-order defect:
`a\u0301b` met the raw 3-character minimum before normalizing to 2 characters;
a decomposed username with normalized length 30 could fail the raw maximum.
This finding is retained and not replaced by earlier passing test results.

Revision files: `accounts/serializers.py`, `accounts/tests/test_auth.py`.
`NormalizedUsernameField` now converts string input to NFC before DRF field length
validators run. Added regressions rejecting normalized length 2 and accepting a
60-codepoint decomposed input normalized to exactly 30 characters.

Commands (from repository root):
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py test accounts --settings=config.test_settings --verbosity 1`:
  **28/28 passed**, 0.408 seconds; includes both new boundary regressions.
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py makemigrations --check --dry-run --settings=config.test_settings`:
  **passed**, no changes detected.
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py check --settings=config.test_settings`:
  **passed**, no issues (0 silenced).

Independent revision re-review/re-verification remains parent-managed and pending.
No runtime/real-service checks were performed, for the unchanged task restrictions
listed above. No F implementation or files outside backend ownership were changed.
