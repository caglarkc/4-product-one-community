# FIRST community redesign — 20 September 2026

## Scope and design

User requested public community projects on home and a full modern GitHub-inspired redesign. Previous warm palette is replaced by dark graphite surfaces, blue links, green actions, restrained monospace metadata and repo-inspired project cards. FIRST/tasarim-dili.md and the frontend skill now reflect the same direction.

## Backend

GET /api/auth/projects/?page=N returns fixed 12-item pages, total count and previous/next page. Active shares from active owners only, deterministic newest-first ordering, requester-independent. Summary allowlist contains consented title/description, canonical classification labels/codes and dates; no repository or account data/README. No GitHub calls in feed, separate rate limit. Existing POST/detail/authorization preserved. No model or migration changes.

## Verification boundary

Source/diff inspection only under repository preference. No tests, lint/typecheck, local build or browser. Standard deployment build/check/health steps are part of delivery. Visual rendering and live user scenarios remain unverified.

## Delivery

Frontend delivered shared ProjectCard, real paginated home feed, loading/error/empty states, public retry after session invalidation and page focus management. Navigation/auth gates are retained. Independent source review accepted without P0/P1/P2 findings; manager verified final diff and removed-token usage.

Application commit `10d35d06f01de1b05f82748937e642fecf1d2d5d` pushed to origin/main; remote hash matched. Standard deployment pulled that commit and released `20260920T135812-10d35d06f01d`. Django checks passed; no pending migrations; PostgreSQL/Redis connections and all three container health checks passed; health returned `{"status":"ok"}`. Persistent data and other projects preserved.

Vercel status for application commit `10d35d0` reported success: “Deployment has completed”. No manual frontend deployment was started.
