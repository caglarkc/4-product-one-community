# FIRST persistent project and repository snapshots

User explicitly overrides previous live GitHub verification after project creation. Project cards, detail and edits must use local backend data only. Repository selection imports the complete authorized collection on first read and persists it; later reads use that snapshot including empty collections. Only explicit refresh fetches again.

## Contract

- Project stores repository_name/repository_url in addition to existing privacy, title, description, taxonomy and owner-approved README. Detail/mine/public serializers use DB only. Private publication never exposes repo name/link. Public publication privacy is its saved import state, not a live GitHub claim. Later GitHub changes do not silently update/hide local publication. Existing projects keep stored data; unknown name/link remain blank with no provider backfill.
- PATCH checks owner/session/email and classification, no GitHub binding/provider dependency. Archive-only existing behavior retained.
- GET projects/github/status is local credential/config status, not live grant verification.
- GET projects/github/repositories imports if no snapshot; else DB. POST {} explicitly refreshes. Response repositories,cached_at. Failure keeps prior data. Snapshot isolated by credential/account; deletion cascades on revoke/reset. Callback reconnect invalidates provider-derived snapshots. Generation guard prevents old external responses overwriting newer refresh/reconnect results.
- Explicit Preview preparation may import chosen repo + README before any project exists. Backend persists exact authorized preview with unique preview_token. Create includes token and selection IDs; publishes only this exact saved snapshot, no network. Submitted excerpt empty or exact prepared excerpt. Successful refresh/reprepare invalidates old consent; stale token rejected, not silently rebound to newer privacy/name. Preview consumed once under locks.
- Frontend initial GET, explicit POST refresh, saved timestamp, error/retry and draft preservation. Refresh discards prepared consent; stale preview requires prepare again. Onboarding must not refresh silently or loop forever on cached empty list.
- Additive 0003 migration; no provider data backfill or old migration edits. Manager deploys standard flow. Source/diff review only, no tests/lint/typecheck/local build/browser.

## Review

Independent review of ownership/session consistency, exact preview consent, cache race and failure preservation, response privacy, additive schema, reset cascade and all frontend consumers. Inventory documents all remaining GitHub APIs/redirects/assets from final source.
