# FIRST deployment

Frontend: https://first.alicaglarkocer.com on Vercel. GitHub pushes trigger its configured frontend build. The owner explicitly chose to track frontend `.env.production` in this private repository. It contains only three server-side proxy settings; backend SMTP, database and Django secrets are not committed. Root `.gitignore` remains in place to exclude dependencies and unrelated local secrets; only this production config is explicitly tracked.

Backend: Hetzner Docker Compose project `first`, deployed below `/opt/first/backend`. Django listens on loopback port 18081; PostgreSQL and Redis expose no host ports. Existing host nginx forwards only `/api/auth/` on its HTTPS IP virtual host to FIRST. Other virtual hosts/routes are preserved. The existing IP TLS certificate and renewal service are shared with the already configured host; renewal must remain operational. Auth requests require the frontend HMAC assertion, CSRF and secure cookies.

## Routine deployment

From the repository root:

```sh
./send-machine --dry-run
./send-machine
./send-machine --check
```

Python 3, SSH key access and the verified host entry in known_hosts are required. Root `.env` supplies `hetzner_sunucu_ip`, `FIRST_AUTH_PROXY_SECRET` and optional `FIRST_SSH_USER` (default root). The proxy secret must match frontend `.env.production`. SMTP overrides are optional; existing remote settings are preserved. The initial deployment copied only SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD and EMAIL_FROM from the remote Immense configuration, mapping EMAIL_FROM to SMTP_FROM with STARTTLS on port 587. No Immense file was modified.

The script uploads only allowlisted backend runtime files, migrations and deployment scripts. No frontend, tests, venv, node_modules, Git history, other product, or raw .env file is sent. Future backend assets/dependency files outside that allowlist must explicitly be added to `source_files()` before deployment. Configuration is sent separately over SSH and stored with mode 600.

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
was exposed to the frontend. `send-machine` forwards only the four OAuth settings
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
