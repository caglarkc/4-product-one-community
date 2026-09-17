# F — account management backend writer evidence

Owner: backend_writer; no frontend, graph or Git writes. Files:
`accounts/account_views.py`, `accounts/views.py`, `accounts/urls.py`,
`accounts/models.py`, `accounts/migrations/0003_user_email_change_nonce.py`,
`accounts/security.py`, `accounts/tests/fakes.py`, `accounts/tests/test_account.py`,
`README.md`.

Implemented password reset/request-confirm, password change and reauthentication,
profile PATCH, verification/resend, confirmed email change with original-address
notice, own-session listing/individual revocation and authenticated bulk revocation.
Every mutation uses inherited explicit CSRF protection; protected endpoints use
session authentication and return 401 without a session. GET link endpoints are 405.

Command history (repository root):
1. `FIRST/backend/.venv/bin/python FIRST/backend/manage.py makemigrations accounts --settings=config.test_settings`:
   passed; generated 0003 durable email-change nonce.
2. `FIRST/backend/.venv/bin/python FIRST/backend/manage.py test accounts --settings=config.test_settings --verbosity 1`:
   baseline **35/35 passed**, 0.429s; expanded first run **53/53 passed**, 0.819s;
   stronger concurrency/session/partial-mail cases **59/59 passed**, 0.898s.
3. Final same suite: **62/62 passed**. Covers missing token code, resend SMTP failure,
   and verified proxy IP for reset admission in addition to the preceding cases.
4. `FIRST/backend/.venv/bin/python FIRST/backend/manage.py makemigrations --check --dry-run --settings=config.test_settings`:
   passed; no changes detected.
5. `FIRST/backend/.venv/bin/python FIRST/backend/manage.py check --settings=config.test_settings`:
   passed; no issues (0 silenced).

No failed test attempts occurred in the F writer iteration. Earlier stage failures
remain preserved in stage-B evidence. Independent review/verification is pending;
this record is writer evidence, not a claim that independent gates have passed.

Acceptance evidence lives in `accounts/tests/test_account.py`: real CSRF enforcement
on every added mutation, anonymous authorization, profile write whitelist/age/NFC,
initial registration counts toward resend quota, 60s and 5/hour gates, 24h expiration
simulation, one-time tokens, GET does not verify, generic reset bodies/status and
sanitized SMTP errors, existing/unknown reset quotas, reset expiration/UID/version,
password validation before consumption, unusable-password recovery, shared proof
limiter, recent-proof expiry, two-session reset revocation, expired/revoked list
filtering, cross-user session ownership, opaque schema, email old/new addresses,
superseded tokens, uniqueness recheck/no merge, stale registration tokens, SMTP
partial failure cleanup, and an in-flight request whose durable version is revoked
before its locked mutation guard.

Technical choices: reset UID is decimal user ID text; failed mail reservations count
against the send budget; email-change durable nonce supersedes prior pending tokens;
all sensitive mutations revoke by durable registry/version without depending on
Redis cleanup. Email change can require two SMTP operations, 10 seconds each; main
was notified that the frontend proxy timeout must become 30 seconds in stage G.
Synchronous SMTP can expose timing differences; only response schema/status account
enumeration resistance is claimed. External email cannot be transactionally recalled:
a sent new-address link is deleted/invalid if later old-address notification fails.

Not verified and why: PostgreSQL row-lock/concurrent transaction behavior and actual
migration; Redis Lua atomicity, actual TTL scheduling/failure recovery; real SMTP
delivery/timing; browser E2E/proxy behavior; deployment/container runtime. User forbids
starting such services in this task. Tests use isolated memory SQLite, FakeRedis and
locmem mail with in-process clients, with no listening service or network email.

## F independent review failure and revision — partial save scope

Independent F review **failed P1**: `User.save(update_fields=...)` previously added
email and username fields unconditionally. A real Django `update_last_login` signal
with a stale user instance could therefore restore an old address after another
request confirmed an email change, while leaving the new verified flag/version.
The earlier 62 passing tests did not detect this race; that failure is retained.

Revision files: `accounts/models.py`, `accounts/tests/test_account.py`.
Partial saves now preserve their requested field scope: email normalization occurs
only for a requested email write or full save; username normalization and its derived
key are written only for a requested username write or full save. A last-login-only
write never includes identity fields. Three regressions exercise Django's actual
`update_last_login(None, stale_user)` against newer persisted identity/version,
username-only normalized writes and email-only writes preserving a newer username.

Commands from repo root:
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py test accounts --settings=config.test_settings --verbosity 1`:
  **65/65 passed**.
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py makemigrations --check --dry-run --settings=config.test_settings`:
  **passed**, no changes detected.
- `FIRST/backend/.venv/bin/python FIRST/backend/manage.py check --settings=config.test_settings`:
  **passed**, no issues (0 silenced).

Independent revision re-review and verification remain pending with the parent.
The simulated stale-instance regression uses SQLite and does not claim a real
PostgreSQL concurrent transaction test. Other not_verified boundaries are unchanged.
No G/frontend work was started.
