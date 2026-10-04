# STEP hosted backend

The backend-only mirror retains `STEP/backend/` and this directory. It does not
include the web app, desktop tracker, local simulator environment, or runtime data.
The frontend is hosted separately at `https://step.ack-techs.com` on Vercel.
The backend is `https://step-api.ack-techs.com/api/v1/` on Hetzner.

Run from the mirror root, normally `/opt/step`:

```bash
python3 STEP/deploy/configure_hosted.py
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml build backend
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml up -d db
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml run --rm backend python manage.py migrate --noinput
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml run --rm backend python manage.py collectstatic --noinput
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml up -d --wait
```

Only the API loopback port `127.0.0.1:18085` is published. PostgreSQL has no host
port. STEP owns its database and private-file volumes; never run `down -v` during
an update. `STEP/.env.hosted` is generated on the host with mode 0600 and must be
backed up securely together with the database and private files. It is not in Git.
Keep `/opt/step/STEP/static` readable by Nginx and owned by container UID 1000.

Install `nginx-http.conf` into a separate enabled site, verify `nginx -t`, issue
the exact hostname certificate using the existing webroot `/var/lib/server-ip-acme`,
then install `nginx.conf`. The HTTPS proxy overwrites forwarded headers. Do not
publish the backend port externally or enable trusted headers behind an untrusted
proxy. The final template uses the existing `ack_api_domain` query-free log format.

The host runs **live mode with DEBUG disabled and no simulator**. Missing SMTP,
NetGSM and Iyzico credentials, university domains, pricing rules and payment
capabilities remain unavailable; infrastructure readiness does not mean financial
release readiness. No fake accounts, prices, credits, jobs or provider keys are
created. An operator can be created interactively with:

```bash
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml run --rm backend python manage.py step_operator --email YOUR_EMAIL --name YOUR_NAME
```

An existing database cannot be switched between test/live modes or providers.
Keep the live database; use a separate temporary test database for automated tests.
Configure the web production API as `https://step-api.ack-techs.com/api/v1/`.
Preview/default Vercel origins are deliberately not allowed to share live sessions.

## Manual source sync and deploy

On a machine with read access to the original repository and write access to this
mirror:

```bash
git pull --ff-only
python3 .backend-sync/sync.py
```

Then on Hetzner, with read access to the mirror:

```bash
cd /opt/step
git pull --ff-only
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml build backend
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml run --rm backend python manage.py migrate --noinput
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml run --rm backend python manage.py collectstatic --noinput
docker compose --env-file STEP/.env.hosted -f STEP/deploy/compose.production.yaml up -d --wait
```

Hetzner uses its existing GitHub authentication; this organization disables
repository deploy keys. Source pushes and mirror sync do not restart services
automatically. Review migrations and take a backup before later schema changes.
