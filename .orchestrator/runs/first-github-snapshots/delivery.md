# FIRST persisted repo and project data — 20 September 2026

## Delivered behavior

Existing published project list/mine/detail/edit and final create use backend DB only. Project stores repository name/URL/privacy plus approved text, with private repository name/link suppressed. Old unknown link fields remain blank; no provider backfill. Subsequent GitHub changes do not auto-change published snapshots.

Credential-scoped repository collection persists first successful import including empty list; later reads never auto-refresh. Explicit POST refresh keeps previous successful list on errors. Generation and user/credential checks protect overlapping requests/reconnect/unlink. Prepared consent is invalidated at refresh start, and rows deleted on successful refresh. Explicit prepare reads cached metadata and fetches only README (plus token refresh if required); exact preview UUID/credential/selection/generation binds final publication, consumed transactionally. Credential deletion cascades new cache/prepared records. Callback invalidates them. Local status performs no provider call.

Frontend shows saved-list timestamp, explicit refresh with draft preservation, snapshot semantics, and exact preview token handling. Existing project edit does not require GitHub binding. Manage screen provides explicit installation/reauthorize/refresh controls, no silent provider redirect/list refresh.

Complete remaining API/redirect/asset inventory: FIRST/contracts/github-connections.md. Includes login/App OAuth, first/manual collection import, pre-creation README prepare, conditional provider token refresh, explicit grant revocation, manual admin backfill, avatar assets and clicked links.

## Review and limits

Independent review found no P0/P1/P2 findings; manager read final source, migration/model alignment, call graph and inventory. Reviewer documentation followup applied: manage navigation and explicit reauthorization described accurately. No tests, lint/typecheck, local build, browser or live user/OAuth scenario run. Race handling reviewed in source, not experimentally verified.

## Deployment

Application commit 03626172abfb4c1cc3367c3e8c8175dd1fc16223 pushed to origin/main and remote hash matched. Standard backend deployment applied projects.0003_repository_snapshots successfully; no destructive/data-backfill operation. Backend release 20260920T184438-03626172abfb healthy; Django check, PostgreSQL/Redis connectivity and all three container health checks passed, health status ok. Vercel automatic deployment for 0362617 reported success.
