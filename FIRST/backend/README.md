# FIRST backend

Django 5.2 / DRF normal auth API. Production settings require PostgreSQL and Redis;
SMTP is configured using environment variables. No real credentials belong in Git.
Use `.env.example` for required names. Docker Compose runs Django/Gunicorn,
PostgreSQL and password-protected Redis together; SMTP remains an external service.
Compose supplies `.env` to the backend at runtime. Migrations run explicitly before
starting the backend. Database and Redis data persist in named Docker volumes.

## Docker startup

Run these commands from `FIRST/backend` with Docker Engine and Compose available.
The prepared local `.env` contains private settings and must stay outside Git and
the Docker image. For a fresh checkout, copy `.env.example` to `.env`, fill every
blank required credential and replace the example frontend origin before starting.
Use distinct random hex values for Django (at least 50 characters), PostgreSQL and
Redis credentials. `AUTH_REDIS_URL` must match `REDIS_PASSWORD` and address service
`redis`; `POSTGRES_HOST` must be `db`. Existing database volumes retain their original
password: changing `.env` alone does not rotate a provisioned database credential.

```sh
chmod 600 .env
docker compose --env-file .env config --quiet
docker compose --env-file .env build backend
docker compose --env-file .env up -d --wait --wait-timeout 120 db redis
docker compose --env-file .env run --rm --no-deps backend python manage.py check
docker compose --env-file .env run --rm --no-deps backend python manage.py migrate --noinput
docker compose --env-file .env run --rm --no-deps backend python manage.py migrate --check
docker compose --env-file .env run --rm --no-deps backend python manage.py shell -c 'from django.db import connection; from accounts.security import client; connection.ensure_connection(); assert client().ping(); print("PostgreSQL and Redis connections passed")'
docker compose --env-file .env up -d --wait --wait-timeout 120 --no-deps backend
curl --fail http://127.0.0.1:18081/health/
```

The backend is available on host loopback port `FIRST_BACKEND_PORT` (default 18081);
PostgreSQL and Redis have no published ports. If the port is changed, use that port
in the health request. `docker compose --env-file .env down` stops the stack while
retaining data; `down --volumes` deletes its persistent data. Do not source `.env`
as a shell script or print rendered Compose configuration containing credentials.
The example Redis URL uses Compose interpolation; a concrete authenticated URL is
also supported, as in the prepared local file.

The prepared configuration targets the existing HTTPS frontend origin. Browser
auth requires the Next.js proxy and secure cookies; a successful HTTP health check
alone does not verify login. Set the backend `AUTH_PROXY_SECRET` to the same secret
used by the frontend and set its trusted IP header as described below. Local Docker
startup does not update Vercel or the existing Hetzner environment. For production
releases, use the existing `send-machine` workflow in [deployment.md](../deployment.md),
which manages the separate server environment and runs migrations before startup.

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

## Live deployment

Deployment instructions and current verification evidence: [deployment.md](../deployment.md). Email change additionally reserves a stable requester budget (60 seconds between attempts, 5/hour per user, 30/15 minutes per trusted IP) atomically before destination admission and SMTP. Changing destinations cannot bypass the requester limits.
