# FIRST web

Next.js 16.3.5 + React 19.3.0 + TypeScript. Node.js 20.9+ is required; this delivery's code checks used Node 25.8.2. Dependencies are pinned in package-lock.json.

`npm ci`, `npm test`, `npm run lint`, `npm run typecheck`, `npm run build` run dependency installation and static/in-process checks. This task does not start an application server.

Routes: `/giris`, `/kayit`, `/hesap` (temporary truthful session status). Root redirects to `/hesap`; account management belongs to the next stage. UI calls real `/api/auth/*/` endpoints. No social login or fake backend data is present in product code.

Set server-only `BACKEND_URL` to the fixed Django HTTP(S) origin, without path, credentials, query or fragment. Missing/invalid config fails closed with 503; builds do not contact Django. `/api/auth/[...path]` preserves the Django-required final slash, forwards Cookie/Origin/Referer/X-CSRFToken, preserves separate Set-Cookie values and disables caching. Client requests fetch a fresh CSRF token before every mutation, including anonymous register/login. Session credentials never enter browser storage.

Deployment prerequisites: HTTPS frontend for Secure cookies; backend `CSRF_TRUSTED_ORIGINS` includes the frontend origin and `ALLOWED_HOSTS` includes backend host. Cookie Domain must remain unset/compatible with frontend host; backend paths `/` and SameSite=Lax work with the same-origin proxy. Backend IP limiter sees proxy REMOTE_ADDR: trusted ingress/IP handling needs explicit deployment verification, and arbitrary client X-Forwarded-For is deliberately not trusted here.

Not verified in this task: listening runtime, actual PostgreSQL/Redis/SMTP, proxy infrastructure/client-IP forwarding, browser E2E, deployed HTTPS and cookie delivery. Passing component/build checks is not evidence that live services work.

Proxy implementation reference: https://nextjs.org/docs/app/getting-started/route-handlers .

Optional per-client IP mode: configure the same server-only `AUTH_PROXY_SECRET` (at least 32 characters) on Next and Django, and set `AUTH_CLIENT_IP_HEADER` on Next to the exact header overwritten by the trusted ingress. Configure both frontend variables or neither. Ingress MUST replace any client value and prevent direct untrusted access to Next; merely choosing a header name does not establish trust. Never expose the secret with `NEXT_PUBLIC_`. Missing/invalid configuration or absent/malformed/multiple IP values fails closed with 503. Next generates HMAC-SHA256 assertions bound to IP, timestamp, HTTP method and Django path; incoming assertion headers are never copied. Django checks signatures and timestamp freshness. With neither variable, incoming IP assertion headers are ignored and Django uses REMOTE_ADDR (proxy budget aggregates by egress). Deployment trust, clock sync and real per-client behavior remain not_verified.

For an actual Vercel deployment, its documented overwritten `x-forwarded-for` can be configured as `AUTH_CLIENT_IP_HEADER` (https://vercel.com/docs/headers/request-headers). This example is not safe on an unprotected local/self-hosted server accepting that client header directly. Validate ingress behavior before enabling signed mode.
