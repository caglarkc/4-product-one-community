# FIRST backend

Django 5.2 / DRF normal auth API. Production settings require PostgreSQL and Redis;
SMTP is configured using real environment files under the owner’s private-repository protocol in `.agent/rules.md`; never print credentials or include them in images. Docker Compose runs Django/Gunicorn,
PostgreSQL and password-protected Redis together; SMTP remains an external service.
Compose supplies `.env` to the backend at runtime. Migrations run explicitly before
starting the backend. Database and Redis data persist in named Docker volumes.

## Docker startup

Run these commands from `FIRST/backend` with Docker Engine and Compose available.
The real `.env` files are managed directly under `.agent/rules.md`; preserve server-specific values. Real env inclusion in the verified private remote follows the owner’s explicit protocol; env files stay outside Docker images. For a fresh environment, configure the actual `.env` before starting; example files are not a completed setup.
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

The configured browser calls `https://167.235.158.118/api/auth/` directly, with
an opaque Redis session in Authorization: Bearer and session-bound CSRF. There
is no Next API proxy, shared HMAC secret or cookie authentication. Exact-origin
CORS allows the configured frontend. Old cookie users must sign in again.
Use `send-machine` for pushed main checkout, preserved server configuration,
Docker build/migrations and built-in deployment health checks.

Implemented normal-auth endpoints under `/api/auth/`: `csrf/`, `config/`,
`register/`, `login/`, `me/`, `logout/`, `profile/`, `reauthenticate/`,
`password/reset/`, `password/reset/confirm/`, `password/change/`, `email/resend/`,
`email/verify/`, `email/change/`, `sessions/`, `sessions/<uuid>/`,
`sessions/revoke/`. See `../contracts/auth-api.md` for request and response shapes.
Google/GitHub OAuth and GitHub App repository authorization are implemented; config reports actual availability.

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

With `TRUST_NGINX_PROXY=true`, nginx must overwrite X-Real-IP and
X-Forwarded-Proto; the Docker backend must remain loopback-only. Arbitrary
X-Forwarded-For is not used. This is the configured production ingress.

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

## Google giriş ve profil tamamlama

`GOOGLE_ENABLED=true`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` ve Google Console ile birebir
aynı `GOOGLE_REDIRECT_URI` sunucu ortamında tanımlanır. Secret frontend'e verilmez.
`django-allauth[socialaccount]==65.19.4` Google JWT doğrulaması ve kalıcı `SocialAccount`
kimliğini sağlar; deploy sırasında paketle gelen account/socialaccount migration'ları uygulanır.
Allauth'un HTML/link/unlink URL'leri açık değildir; mevcut FIRST JSON ve oturum sınırı korunur.

- `POST google/start/`: CSRF korumalı `{remember_me?, purpose?: "login" | "reauth"}`;
  `{authorization_url}` döner. `openid email profile`, PKCE S256 ve nonce kullanır.
- `GET google/callback/?code=...&state=...`: session-bound, Redis'te tek kullanımlık
  10 dakikalık state; `{status: "authenticated" | "profile_required" | "reauthenticated", user?}`.
  Tarayıcı callback'i Next.js aynı-origin sabit rota üzerinden buraya aktarır.
- `GET google/signup/`: 10 dakikalık oturuma bağlı bekleyen profil, `email_verified` ve
  `email_editable` döner. Yeni kullanıcı henüz oluşturulmamıştır.
- `POST google/signup/`: normal zorunlu profil alanları ve opsiyonel telefon; şifre kabul etmez.
  Güvenilir Google e-postası değiştirilemez; eksik/güvenilir olmayan adres kullanıcıdan alınır
  ve kayıt tamamlanmadan FIRST e-posta kanıtı zorunludur (`email_verification_required`).
  Kanıt öncesinde aktif kullanıcı/sosyal kimlik oluşturulmaz. Böyle bir adres kanıt olmadan mevcut hesapla eşleştirilmez.
- `POST google/email/request/ {email}` bekleyen Google kaydı için 10 dakikalık FIRST e-posta
  kanıtı gönderir (`/google-eposta-dogrula?key=...`). `POST google/email/verify/ {key}` aynı
  tarayıcıdaki bekleyen Google oturumunu gerektirir; mevcut hesap varsa kanıt sonrasında bağlar
  ve giriş yapar; yoksa kayıt profili doğrulanmış/değiştirilemez e-postayla devam eder.
  Hesap güvenlik sürümü değişirse eski kanıt geçersizdir.

Google'ın doğrulanmış Gmail veya Workspace e-postası mevcut hesapla otomatik eşleşir.
Önceden doğrulanmamış hesabın eski oturumları, yerel şifresi, kurtarma token sürümü ve
önceden bağlanan sosyal kimlikleri geçersizleştirilir; gerçek e-posta sahibinin Google kimliği
bağlanır. Sonraki girişler provider/sub kimliğini esas alır. Google bağlama/kaldırma endpoint'i yoktur.
Hassas işlemler için `purpose=reauth` yalnız zaten bağlı Google kimliğini kabul eder;
Google `auth_time` alanı yeni doğrulamayı kanıtlamalıdır. Provider access/refresh token'ları saklanmaz.

Test: `python manage.py test accounts --settings=config.test_settings`.
`test_google.py` sahte Redis ve token exchange kullanarak akışı, ayrıca RSA ile imzalanmış JWT'lerle
allauth imza/issuer/audience/süre/nonce kontrollerini test eder; gerçek Google hesap etkileşiminin yerine geçmez.

Gunicorn erişim logları yalnız method, sorgusuz URL path, durum ve süre içerir; OAuth code/state, cookie ve referrer loglanmaz.

## Listing participation integration — 21 September 2026

`projects` adds listing needs, immutable participation methods, visibility grants, applications/invitations, site notifications and explicit Issue/PR operations. Migration `0004_participation` is additive; existing legacy listings default to applications closed. Ordinary project reads remain database-only. GitHub effects have persisted decisions, stable identities and retry reconciliation; automatic invitations require provable current protections and fail closed otherwise.

Contract: [participation-api.md](../contracts/participation-api.md). Operator/product behavior: [ilan-katilim.md](../ilan-katilim.md). Tests, deployed revision and live verification boundaries: [integration run](../../.orchestrator/runs/first-listing-participation/run.json). The test transport follows the current Bearer session header; no cookie/proxy authentication was reintroduced.

## Independent teams, snapshots and public tasks

Apps `teams`, `showcase`, `tasks` each include an initial schema migration. URL roots are `/api/auth/teams/`, `/api/auth/showcase/`, `/api/auth/tasks/`; see `FIRST/contracts/*-api.md`. Team ownership is checked before account deletion and GitHub revocation. Selected-file original bytes and safe previews are private PostgreSQL snapshot fields covered by existing backups; no public media bucket or raw download endpoint exists. Expired unpublished previews are removed on the next prepare operation. Public task read paths recheck GitHub repository privacy before exposing cached Issue content, and ambiguous creates reconcile a persisted request marker rather than issuing another POST.

Docker installs libseccomp2, Pillow and pypdfium2 for isolated resource-limited raster conversion. Converter stdin/stdout has bounded content, environment has no credentials, and filesystem/network/process syscalls are denied after dependencies load. Some PDF fonts can differ, unsupported/oversized content is rejected, and preview consent is required. Converter compatibility and 512MiB container headroom have not been tested by this source-only delivery.
