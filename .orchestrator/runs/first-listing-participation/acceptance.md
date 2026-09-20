# FIRST listing participation acceptance

Approved order: backend and GitHub provider helpers → frontend → independent review → tests → acceptance → push/deploy/live checks. User explicitly authorizes tests, GitHub push, remote pull/rebuild and live site checks.

## Product acceptance

- One active listing per repository, one need category and one immutable participation method.
- Feature/bug requires current state, expected outcome and existing/new GitHub Issue.
- Application acceptance sends GitHub invitation; GitHub acceptance is distinct from FIRST acceptance.
- Automatic participation fails closed unless supported live repository protections are proven again at invite time.
- PR-first public only; numeric author/repo identity and reviewed head SHA before merge; merge-only distinct from merge+invite.
- Public/link/selected visibility, selected-viewer grants distinct from participation invitations and private repo access.
- Closed applications excluded from discovery; prior applications remain evaluable; owner controls closure, not PR or application events.
- Pending/failed remote effects remain durable and retryable; partial merge/invite failure reconciles safely.
- Open PRs/related Issue and invitation status supported; contributor statistics and chat deferred.
- Category, need and participation filters; dashboard, notifications and full form/error states.

## Verification plan

Backend isolated tests: uniqueness, visibility matrix, ownership, verified email/GitHub UID checks, CSRF, state transitions, no automatic reopen/close, Issue idempotency, PR SHA and numeric identity, live protection changes, private read-access gates, provider failure and partial success recovery. Existing stale project test fixtures will be updated to current snapshot contracts; security assertions retained.

Frontend: form requirements/private PR exclusion, consent and preview handling, filter requests, private safe links, dashboard decision eligibility, reviewed SHA, invite next step, loading/errors, typecheck/lint and relevant tests. No extra local production build; Vercel builds pushed source.

Deployment: exact pushed commit and clean remote fast-forward, additive migration, preserved persistent data, built-in health, live API authorization/visibility checks and real site navigation/form inspection. No production GitHub merge, invitation or new external Issue used as a test without a designated fixture; report that limit accurately.

## Initial read-only operational evidence

- Verified origin caglarkc/4-product-one-community is private and default branch main.
- Existing GitHub App installations already grant administration/write, contents/write, issues/write, pull_requests/write and metadata/read; no settings expansion needed based on initial read.
- One existing FIRST test listing identified by exact UUID 872f07fe-7871-4722-a831-b4e2b7b6a48a (repository numeric ID 883047055). User permits removing this FIRST listing. Do not delete GitHub repository, issues, PRs or arbitrary future listings.
- Existing source maps are stale; actual source and migrations are authoritative. No map redesign included.
