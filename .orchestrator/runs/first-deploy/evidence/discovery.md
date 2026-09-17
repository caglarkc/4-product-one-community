# FIRST deployment discovery — parent observation record

This note is a redacted backfill of actual observations reported by the parent agent. The ledger writer did not re-run SSH.

- User authorized remote deployment and specifically backend-only transfer via `./send-machine`.
- Parent accessed the authorized host through SSH using private root configuration. No raw host address or credentials are recorded here.
- Existing nginx listens on 80/443; a valid IP certificate exists under `/etc/letsencrypt-evkarnesi`.
- Existing loopback listeners include 18080 (evkarnesi) and 8787 (ajanda); public listeners include 3000, 8080 and 9080.
- Port 18081 was observed free and selected for isolated FIRST backend ingress.
- Discovery did not modify or stop other containers/applications.
- Deployment, frontend integration, real PostgreSQL/Redis/SMTP tests and runtime verification remain separate pending work.
- Source catalog refreshed into this run only. Maps are stale and treated as hints; actual source/configuration takes precedence.
