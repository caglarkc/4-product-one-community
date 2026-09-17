# FIRST backend

Django 5.2 / DRF normal auth API. Production settings require PostgreSQL and Redis;
SMTP is configured using environment variables. No real credentials belong in Git.
Use `.env.example` for required names. The container reads `.env`; PostgreSQL,
Redis and SMTP must be supplied by the target environment. The compose file does
not provision those services or run migrations automatically.

Implemented normal-auth endpoints under `/api/auth/`: `csrf/`, `config/`,
`register/`, `login/`, `me/`, `logout/`, `profile/`, `reauthenticate/`,
`password/reset/`, `password/reset/confirm/`, `password/change/`, `email/resend/`,
`email/verify/`, `email/change/`, `sessions/`, `sessions/<uuid>/`,
`sessions/revoke/`. See `../contracts/auth-api.md` for request and response shapes.
OAuth and provider connection are not implemented. Config reports both unavailable.

## Security storage

PostgreSQL stores users and session revocation records. Redis stores signed session
contents, rate counters and hashed-key temporary verification tokens. Session
contents never fall back to a process-local cache or database. Authentication checks
persistent registry revocation, expiry and user security version on every request.
Normal sessions last 24 hours, remembered sessions 30 days; expiry is absolute.

The shared password proof helper reserves an account attempt under a Redis lock
before hashing. Concurrent proof requests return 429 while the lock is held (30s
lease); failures remain counted for 15 minutes and success clears the counter.
The IP budget is 30 requests/15m, account budget is 5 failed attempts/15m. Expensive
hash operations must complete within the lease; real Redis concurrency remains a
required environment check. By default only REMOTE_ADDR is trusted; arbitrary
X-Forwarded-For and X-First-Client-* assertions are ignored.

Optional per-client proxy attribution requires the same `AUTH_PROXY_SECRET` on
backend and frontend (at least 32 characters). Frontend also configures
`AUTH_CLIENT_IP_HEADER` to a single IP header that its trusted ingress always
replaces. Backend then requires every `/api/auth/` request to carry
`X-First-Client-IP`, `X-First-Client-Time`, `X-First-Client-Signature`.
The signature is HMAC-SHA256 hex over exact UTF-8 text:
`ip + "\n" + unix_seconds + "\n" + HTTP_METHOD + "\n" + request.path`.
The backend validates a single IP, integer timestamp within 60 seconds, and the
signature with constant-time comparison. It canonicalizes the verified IP before
rate counting so equivalent IPv6 representations share a budget. Missing, invalid,
stale or method/path-mismatched assertions return 403 `invalid_proxy_assertion`.
A configured short secret fails startup. Assertions cannot substitute for CSRF;
the usual cookie/origin/token checks still apply. Requests within the 60-second
window can be replayed, so HTTPS and ingress access controls remain required.
Trusted ingress header replacement and matching deployed configuration have not
been verified in this task. Never expose the shared key to browser code.

## Password corpus

Django's `CommonPasswordValidator` uses the common-password list shipped in the
installed Django release (`django/contrib/auth/common-passwords.txt.gz`), with
upstream provenance in Django's auth password-validation sources. This repository
also rejects six locally curated obvious variants; that baseline is not represented
as a comprehensive list of compromised passwords.

For additional compromised-password coverage, a deployment may mount a reviewed
UTF-8/ASCII file and set `AUTH_BREACHED_PASSWORD_FILE` to its absolute path. Each
non-comment line must contain one SHA-256 hash of the exact UTF-8 password. Empty,
missing or malformed explicit files fail startup. No password is sent externally.
The operator must record corpus publisher, acquisition date, license, checksum and
update cadence in deployment records, generate hashes offline from a trusted lawful
corpus, replace the mounted file atomically, and restart workers to load updates.
An external corpus has not been supplied or validated in this task; broad breach
coverage is therefore not verified. Hash algorithms cannot be converted from a
SHA-1-only corpus into SHA-256 without the original values.

## Isolated tests (no listening service)

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py test accounts --settings=config.test_settings
.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.test_settings
.venv/bin/python manage.py check --settings=config.test_settings
```

Tests use in-memory SQLite, a Redis test double and Django's memory email backend.
CSRF tests enable `enforce_csrf_checks=True`. Test settings are exclusively for
isolated checks and must never be used for serving requests. `.venv`, `.env`, local
DBs and bytecode are ignored by Git and Docker build context.

Not verified here: real PostgreSQL constraints/locking/concurrency, Redis Lua
atomicity/TTL/network outages, SMTP delivery, proxy and cookie behavior in a browser,
container runtime, production migration, deployment and browser end-to-end flows.
No backend/frontend service, Docker or local DB/Redis process was started.


## Account management and operational boundaries

Password reset requests use the same generic response for known, unknown, inactive
accounts and SMTP delivery failures, with a sanitized operational warning on mail
failure. Admission limits count every normalized address (5/hour) and trusted client
IP (30/15m). Sending is synchronous: response timing is not claimed to hide account
existence. Reset links use decimal user ID `uid` plus a random Redis token, expire
in 30 minutes, and can be consumed once. Password validation runs before consumption.
A token binds user, email and security version. Reset succeeds for unusable local
passwords as well, allowing email ownership proof to establish a local password.

Verification messages share an atomic address budget of 60 seconds between attempts
and at most 5/hour, including initial registration. Failed SMTP attempts consume the
reservation to prevent rapid retries flooding the SMTP provider. Verification links
last 24 hours and only POST confirmation changes data; GET is not a mutation.

Email change keeps the original address until confirmation, sends a confirmation
to the proposed address and a notice to the original address, and stores a durable
nonce that supersedes earlier pending changes. The token binds that nonce, original
address, user and security version. Confirmation rechecks address uniqueness inside
the user transaction; it never merges accounts. Password reset/change and confirmed
email change increment security version and durably revoke all session records.
Session listings contain opaque IDs, timestamps and the current-session indicator.

Sensitive mutations require password proof within 10 minutes. The user row is locked
and its fresh version/current session registry are checked again inside transactions,
so a request authenticated before a concurrent revocation cannot mint new authority.
Password proof across login, reauthentication and old-password change shares limits.
The user can revoke their own individual sessions; revoking all also requires recent
proof. Profile PATCH is limited to profile fields, and supplied phones remain
unverified. A late request after revocation is rejected even if Redis session content
has not been cleaned up; no Redis deletion is required to persist revocation.

SMTP submission is an external side effect and cannot be rolled back with SQL.
Email change performs two bounded SMTP submissions (10-second timeout each) while
holding the user lock. The frontend proxy must allow at least 30 seconds. If one
submission fails, the nonce change rolls back and the new token is deleted, but an
already delivered email cannot be recalled. Such partial failure is reported as 503;
the delivered new link is invalidated. Real network timing, delivery and transaction
contention remain unverified. A worker/outbox design is future operational work.

Migrate the new schema in the target environment before deployment; migrations have
only been applied against isolated SQLite during this task, never production data.
