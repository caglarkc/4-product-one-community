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
