# FIRST bug-only Issue selection

## Scope and source

Issue binding/creation is now specific to public bug listings. Feature listings retain current state and desired outcome but do not require Issue setup for publication, discovery or applications. Private bug choice is filtered in the UI and rejected by the API. Existing legacy listings remain archivable.

Root cause: repository privacy was already present and used to hide PR participation, but the need-type list had no private/bug rule.

New authenticated POST github/issues accepts the cached repository/installation pair and verifies current GitHub identity/admin/public repository status. It returns at most50 newest open actual Issues via one anonymous search page, excludes PRs, checks response repo/state and fails closed on incomplete data. The selected Issue is revalidated on submission. UI supports explicit loading, empty/error states, existing/new selection and clears stale repo selections/responses.

No schema migration. Historical Issue associations are retained; new feature creation has no Issue fields. No live GitHub Issue creation, invitations or merges are needed for this form verification.

## Verification so far

- Source review by independent acceptance agent passed after archive-only compatibility fix.
- Frontend focused tests18/18 and typecheck passed.
- Live baseline reproduced private repo label and PR filtering working while bug type was incorrectly offered.

Deployment and post-deployment browser outcomes will be added after verification.
