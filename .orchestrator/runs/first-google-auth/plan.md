# FIRST Google implementation plan

User-authorized scope: Google sign-in and staged signup, frontend integration, push,
remote root SSH git pull and Docker rebuild, live verification. Vercel builds on push;
no separate frontend production build is requested. No Google link/unlink UI or API.

## Responsibilities and order

1. Backend owns FIRST/backend except actual .env. Integrate allauth provider, validated
   Google identity, session-bound single-use OAuth handshake, staged signup, identity
   mapping, social reauthentication and migration/tests.
2. Frontend owns FIRST/frontend except actual env files. Google buttons, fixed callback
   route, constrained same-origin proxy, passwordless signup completion and reauth.
3. Root owns current decisions, contract, environment configuration, orchestration,
   independent verification and deployment. Existing deployment config is retained.
4. Independent reviewer checks both sources and security invariants before acceptance.
5. Root pushes accepted changes; remote checkout pulls fast-forward; release script
   creates database/config backups, builds, migrates, health-checks and switches release.
6. Live config/CSRF/OAuth initiation/callback error checks and browser Google flow.
   User-dependent provider login/consent steps are reported separately if not completed.

## Shared API agreed for implementation

- POST /api/auth/google/start/: CSRF; remember_me boolean and purpose login/reauth.
  JSON authorization_url, generated from fixed Google endpoint and server config.
- Google redirect: https://first.alicaglarkocer.com/accounts/google/login/callback/.
  This frontend route forwards only allowed callback parameters to fixed backend
  /api/auth/google/callback/ with cookies and trusted ingress assertion.
- Callback JSON status authenticated / profile_required / reauthenticated, with user
  where applicable. Frontend chooses fixed local destinations, forwards Set-Cookie,
  never exposes upstream redirect or raw provider error/token.
- GET /api/auth/google/signup/: pending profile defaults and email_verified flag.
- POST /api/auth/google/signup/: required profile fields, no password; pending proof
  supplies immutable trusted identity. Untrusted/missing email needs explicit fallback.
- Config exposes provider readiness; user response exposes linked provider names and
  has_usable_password for appropriate reauthentication and password-creation UI.

## Security acceptance

Trust provider subject over mutable email on returning logins. Only trustworthy verified
email may auto-match an unlinked local account. Enforce unique Google subject and active
users; no cross-account reassignment. Matching an unverified local account invalidates
prior sessions/password. New signup validates age >=13 and unique username before final
creation; pending state expires and cannot replay. Reauth must prove the same linked
identity in the same still-valid session. OAuth state/nonce/PKCE, signed identity claims,
CSRF, signed proxy, cookie forwarding, cancellation, service errors and races are tested.

Actual checks and production outcome will be recorded after execution; this plan is not
verification evidence. Credential values never appear in this run.
