# FIRST deployment

Frontend: https://first.alicaglarkocer.com on Vercel. GitHub pushes trigger its configured frontend build. The owner explicitly chose to track frontend `.env.production` in this private repository. It contains only three server-side proxy settings; the owner also explicitly chose to track backend `.env` in this private repository. Backend secrets are never bundled into the frontend or Docker image. Root `.gitignore` remains in place to exclude dependencies and unrelated local secrets; only this production config is explicitly tracked.

Backend: Hetzner Docker Compose project `first`, deployed below `/opt/first/backend`. Django listens on loopback port 18081; PostgreSQL and Redis expose no host ports. Existing host nginx forwards only `/api/auth/` on its HTTPS IP virtual host to FIRST. Other virtual hosts/routes are preserved. The existing IP TLS certificate and renewal service are shared with the already configured host; renewal must remain operational. Auth requests require the frontend HMAC assertion, CSRF and secure cookies.

## Routine deployment

Permanent user instruction: backend changes are delivered through commit/push, remote root SSH pull, Docker rebuild and health checks unless the user explicitly makes an exception. Frontend changes require push only; Vercel automatically builds/deploys. Do not run an extra local production build or manual Vercel deployment. Tests, lint and typecheck remain required as appropriate. Documentation-only changes do not require a backend rebuild.

After accepted changes are committed and pushed to `origin/main`, from the repository root:

```sh
./send-machine --dry-run
./send-machine
./send-machine --check
```

Python 3, SSH key access and the verified host entry in known_hosts are required. Root `.env` supplies `hetzner_sunucu_ip`, `FIRST_AUTH_PROXY_SECRET` and optional `FIRST_SSH_USER` (default root). The proxy secret must match frontend `.env.production`. SMTP overrides are optional; existing remote settings are preserved. The initial deployment copied only SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD and EMAIL_FROM from the remote Immense configuration, mapping EMAIL_FROM to SMTP_FROM with STARTTLS on port 587. No Immense file was modified.

The script verifies clean local backend/deployment sources on main and that GitHub main equals HEAD. It connects via SSH to `/root/first-backend`, checks a clean main checkout and the expected repository origin, runs `git pull --ff-only`, and verifies the same commit. Only allowlisted backend runtime files, migrations and deployment scripts are extracted from that remote commit into the new release. No frontend, tests, venv, node_modules, Git history, other product, or raw .env enters the release archive. The private checkout itself includes the explicitly tracked backend env. OAuth configuration is read separately from the local backend env and merged into the server env; database, Redis and Django secrets are preserved. Future backend assets/dependency files outside that allowlist must explicitly be added to `source_files()` before deployment. Configuration is sent separately over SSH and stored with mode 600.

Each release builds its own image, starts private PostgreSQL/Redis, checks Django, applies migrations, verifies database/Redis connectivity, starts the backend, and checks health before changing the current symlink. Deployments are serialized by a remote lock. Updates back up PostgreSQL and the previous environment. Failed updates restore the previous environment/image when possible; database migrations are not automatically reversed, so schema changes must be backward compatible or accompanied by a deliberate recovery plan. Backup files, images and old release directories are retained; no automatic pruning touches the existing server.

Paths: `releases/<timestamp>-<hash>`, `shared/.env`, `current`, `backups/` below `/opt/first/backend`. The first-time nginx include is `/etc/nginx/snippets/first-auth.conf` in the existing HTTPS IP site. Future `./send-machine` calls update the application; they do not rewrite host nginx or other projects.

## Verification

Initial remote release: `20260917T162358-8c182665a5e4`. All three FIRST containers became healthy; production migrations and PostgreSQL/Redis connectivity checks passed. nginx configuration validation and reload passed. Runtime and frontend integration verification results will be recorded below when completed. No local backend, database, Redis or Docker service was started.

## Remote restart verification — 17 September 2026

The latest observed state supersedes the initial-release notes above. Root SSH found
this repository's clean sparse checkout at `/root/first-backend` on `main`; it was
updated with `git pull --ff-only` to `591b5f8`. No FIRST containers or `current`
symlink existed, while the managed PostgreSQL/Redis volumes and private server env
were retained. A Git archive of that checkout produced release
`20260917T193755-591b5f8c93fe`. Before startup, the server env and PostgreSQL database
were backed up below `/opt/first/backend/backups`. Existing Django, database, Redis,
proxy and SMTP credentials were preserved; the server env remains mode `600`.

The image built successfully. Backend, PostgreSQL and Redis became healthy. Django
checks passed, migrations were already current, and independent checks verified a
real PostgreSQL `SELECT 1`, authenticated Redis `PING`, and JSON HTTP 200 from the
backend `/health/` endpoint.

Two integration problems were found during the initial verification:

- SMTP authentication returns code **534** (`SMTPAuthenticationError`). No email
  was sent. Testing the separately supplied local SMTP credentials on the server
  awaits explicit user approval; no credentials were transferred by that attempt.
- Public frontend `/api/auth/config/` and `/api/auth/csrf/` return another app's
  HTML instead of JSON. The existing HTTPS IP virtual host lacks the FIRST nginx
  include, and `/etc/nginx/snippets/first-auth.conf` is absent. Installing the
  repository's `backend/deploy/nginx.conf` snippet and reloading the shared nginx
  service awaits explicit user approval; no nginx change was executed.

Automatic approval review rejected the two proposed actions above. The containers
are running, but email and public frontend auth are **not verified working**.
Evidence and pending work are recorded in
[the remote run](../.orchestrator/runs/first-remote-docker/run.json).


### Approved integration follow-up

The user subsequently explicitly approved both actions. The HTTPS IP nginx site was
backed up, the tracked FIRST auth snippet was installed, and a single include was
added to its HTTPS block. `nginx -t` and reload passed. Independent checks now confirm
public config and CSRF endpoints return HTTP 200 with valid JSON, and the CSRF token
and Secure/SameSite cookie are present. Docker health, migration, PostgreSQL and Redis
checks still pass. The nginx/public frontend routing problem is resolved.

The user-authorized local SMTP test confirmed local and server settings are identical;
authentication still fails. The provider's precise response is **534 / 5.7.9**, asking
the account owner to log in through a web browser and retry. No email was sent and no
unsuccessful SMTP settings were applied. The account owner must complete that provider
login/security step before SMTP can be rechecked. This is the remaining blocker;
nginx and credential-transfer permissions are no longer pending.


At the user's request, a read-only comparison with the running Immense services
confirmed the SMTP host, port, username, password and sender settings match FIRST.
A Nodemailer `verify()` executed inside the Immense notification container also
failed with **EAUTH 534 / 5.7.9**, requesting browser login. No mail was sent and no
Immense configuration was modified. This independently reproduces the shared
account/provider problem outside FIRST's Django implementation.


### SMTP account rotation completed

The user supplied a replacement Gmail account/application password and explicitly
requested actual backend env files be committed to both existing private GitHub
repositories. Both origin repositories were verified private. FIRST backend `.env`
was committed as `20a6d2b`; SMTP remains excluded from Docker build context. Immense
local `.env` and actual Docker source `.env.docker` were updated. Because its local
history diverged from GitHub, only the SMTP field changes were applied on a separate
checkout of current origin/main and pushed as `d6702f94`, without a force push or
unrelated code changes. The original local checkout retains its historical branch.

On the server, FIRST shared env was updated only after successful SMTP login.
Immense `.env` and `.env.docker` were backed up and only SMTP login/sender fields
changed. Its 16 environment-consuming application services were recreated using
existing images, with no builds or pulls; persistent data services were preserved.
The existing Immense remote source commit was retained (configuration rollout only).

Independent verification now passes: FIRST Django SMTP connection/authentication,
Immense Nodemailer verify, matching runtime SMTP settings, FIRST config/CSRF JSON
and secure cookie, all FIRST containers, all 16 Immense application containers,
Immense gateway health and expected unauthenticated auth-route responses. The SMTP
534 blocker is resolved. No email was sent; inbox delivery and full user account
email flows were not tested.

## Google integration — 18 September 2026

Application commit `1f62e31d7eb6d6879bff764df986ee248ff81ab2` was pushed to main;
GitHub's Vercel status reported successful automatic deployment. No additional local
frontend production build was run. Remote `/root/first-backend` fast-forward pulled
the same commit. Release `20260918T153520-1f62e31d7eb6` built the backend image after
configuration/database backups, applied bundled allauth account/socialaccount
migrations, passed Django/migration/database/Redis checks, and became healthy.
Existing database/Redis volumes and other applications were retained.

Google credentials and enabled flag were added to backend environment only; no secret
was exposed to the frontend. `send-machine` forwarded only the four Google OAuth settings for that release
from backend env for subsequent routine releases. Callback uses the existing frontend
origin `/accounts/google/login/callback/` and the signed `/api/auth/` proxy. FIRST
nginx already disables access logs; Gunicorn now logs paths without query parameters.

Live verification passed: config advertises Google; CSRF JSON and secure cookie;
missing-CSRF start rejection; Google authorization URL with fixed callback, minimal
openid/email/profile scopes, state/nonce/PKCE; cancellation and replay rejection;
pending signup denied without Google proof. Chrome completed real Google sign-in and
returned to the existing FIRST account. A read-only database check confirmed the
account predates the deployment and has one Google identity; it was not duplicated.

87 backend tests, 80 frontend tests, lint/typecheck and independent review passed.
New-user profile completion, third-party-email proof and reauth were covered by
isolated regression tests; no second live Google identity/signup was used. Real
PostgreSQL race contention was not stress-tested. Google Console remains External /
Testing with the intended test user; Branding is incomplete and Publish app is disabled.
No Console settings or publishing state were changed.

## GitHub integration — 18 September 2026

Application commit `aebcb8807fb2b7a971b08f2c09aed4b1199c4725` was pushed to main.
Vercel reported successful automatic deployment; no extra frontend production build
was run. Updated `send-machine` pulled the exact commit from GitHub into the clean
remote checkout and created healthy release `20260918T200008-aebcb8807fb2`.
GitHub configuration was merged while persistent database/Redis/Django settings
were preserved. Database backup, Django/migration checks, PostgreSQL and Redis
connectivity passed; no new migration was needed.

111 backend tests (24 GitHub), 95 frontend tests, lint/typecheck and independent
security/deployment review passed. Live endpoint checks verified provider readiness,
secure CSRF cookie, missing-CSRF rejection, fixed callback with minimal `user:email`
scope and PKCE, cancellation and replay rejection, denied pending signup without
proof, denied anonymous linking and explicit unsupported GitHub fresh reauth.

Chrome completed real GitHub OAuth using the existing signed-in account. The
callback returned 200 and FIRST showed the account with GitHub connected. Read-only
database comparison confirmed the same single user, one Google identity and one
new GitHub identity; no duplicate user was created. Only read-only email access was
requested. A separate new-user live signup and explicit in-account linking were
not performed; these flows are covered by isolated tests. Real PostgreSQL race
contention was not stress-tested.

Startup logs exposed Gunicorn26.2's unused management control socket attempting to
write under `/home/app` in the read-only container. Follow-up `d2cea0c` disables that
socket with the supported `--no-control-socket` option, preserving the read-only
filesystem and existing HTTP/worker/log/health configuration.

The follow-up was pulled and rebuilt as release `20260918T200454-d2cea0cb4c3b`.
All three containers are healthy; PostgreSQL/Redis and migration checks pass.
Fresh backend startup logs contain no control-socket error; `/health/` returns 200.

## Connected-account profile data

Provider display fields are stored as a minimal whitelist in the existing
SocialAccount extra_data field; no schema migration is required. Successful
Google/GitHub login, signup and GitHub linking refresh their own display metadata.
Legacy Google metadata remains empty until a successful provider flow; FIRST email
is never substituted for the provider email.

Existing GitHub connections can be enriched once from their public stable-ID profile:
run `python manage.py backfill_github_profiles --dry-run --limit 50` inside the deployed
backend container, inspect count-only output, then repeat without `--dry-run`.
The command uses fixed HTTPS GitHub API requests, verifies the returned account ID,
imports no public email or token, and fills only missing display fields under locks.
The bound is the first N GitHub identities (1–100), not a paginated bulk migration.
No provider request is made while rendering `/me/` or the account page.

### Connected-account backend rollout — 18 September 2026

Commit `c35afd388a56510b0b7a9e5391787e2096b84267` was pushed and pulled on the
server. Release `20260918T201351-c35afd388a56` built successfully; all three FIRST
containers, Django checks, PostgreSQL/Redis connectivity and migration checks pass.
119 backend tests and 106 frontend tests plus lint/typecheck pass; independent
source review has no material findings.

The bounded GitHub profile dry-run reported one eligible identity and zero errors;
the actual run updated that one display record without changing user ownership or
email. Real Google login subsequently refreshed the existing Google display data.
Read-only database checks confirm the original single user, both provider records,
GitHub name/handle/avatar/profile URL and Google name/email. No raw metadata or
credentials were written into verification output.

Frontend visual verification remains in the active connected-account run until
Vercel automatically publishes the pushed frontend. No local production build or
manual Vercel deployment was initiated.
