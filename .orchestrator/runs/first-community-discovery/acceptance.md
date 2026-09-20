# FIRST community discovery acceptance

Source-review acceptance checklist; runtime tests/browser checks are not authorized for this task.

- Public profile exposes only agreed community identity, bio, optional safe links, catalog skills/interests and invitation preference.
- Discovery excludes inactive, opted-out and GitHub-unlinked accounts; profile direct route remains public for active accounts.
- Invitation preference defaults true for existing/new accounts; opt-out blocks every new invitation in backend, preserves existing pending retries and self-initiated applications.
- Public profile project list obeys public discovery rules; never reveals link-only/selected listings.
- Shared selectable catalog is the source for profile skills and project technologies/required skills; no arbitrary tags.
- Combined people/project query filters support pagination, Turkish search, empty/error states and request bounds.
- Project editor create/edit persists catalog fields without resetting existing values on unrelated edits.
- Owner profile link and new card controls remain clickable above whole-card link; keyboard semantics and focus remain native.
- Bookmark state/list are actor-scoped and idempotent; loss of project access gives no title/content disclosure, removal stays possible.
- Reports require a verified signed-in reporter and accessible target, deduplicate repeated submission, return receipt only, never expose other reports.
- Reporting does not change target visibility, invitations, GitHub resources or access. No moderation interface/automatic penalty.
- Frontend clears protected data across session changes and keeps existing navigation, account, project and participation flows.
- Desktop/mobile layouts reuse FIRST tokens/UI. No external packages needed.
- All migrations are additive/backward compatible. Standard deployment performs its normal build/migration/health checks.
- Excluded: contributors/statistics, team pages, private file showcase, chat, student verification and certificate showcase.

Delivery evidence and limitations must be recorded separately. A source acceptance is not a browser/runtime test claim.
