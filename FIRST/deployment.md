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
