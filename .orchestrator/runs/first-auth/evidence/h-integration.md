# H backend–web integration — PASS

Task h-integration, manager. Dependencies h-review and h-verify passed independently; see their evidence and h-regression.md. Relevant files: FIRST/backend/accounts/{urls,views,account_views,serializers}.py, config/settings.py, FIRST/frontend/src/{lib,components,app}, FIRST/contracts/auth-api.md, both .env.example files.

Commands: source `cat`/`rg` comparison; independent verifier Django URL resolver probe16 frontend call routes passed; full isolated API65 and frontend61 tests plus lint/typecheck/build outputs in h-regression.md. No listening network service.

Confirmed: profile PATCH whitelist and response user align; password old/new/reset uid/token and email key align; sensitive403 triggers password proof then explicit retry; session UUID DELETE and all POST use fresh CSRF;401/token expiry/service errors visible; redirects after invalidation; cookie/Origin/Referer/Set-Cookie/final slash/no-store preserved; optional signed-IP configuration matches server HMAC contract. Verification GET renders confirmation, never changes data. Proxy30s permits two SMTP10s calls but real timing remains unverified. Public config/providers explicitly unavailable; no fake product APIs.

Canonical contract removes obsolete OAuth-active and E-paused statements. Both sample env files contain configuration placeholders, no credentials. Runtime checks intentionally not performed: PostgreSQL concurrency, Redis Lua/TTL/failure, SMTP delivery/timing, trusted ingress and clocks, HTTPS-cookie/browser E2E, Docker/deploy — not_verified. These are environment follow-ups, not failed code gates.
