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

## Completed deployment and live verification

- Application commit `379fe4f049575afa71009cde90112d6de39e2c3e` pushed to origin/main; remote branch hash verified.
- Remote standard release `20260920T214901-379fe4f04957` completed; backend, PostgreSQL and Redis healthy; health endpoint ok. Existing migration checks completed, no new schema migration.
- Vercel commit status: success, Deployment has completed.
- Backend focused projects suite:76/76 passed (7 focused regressions added,2 earlier expectations updated). Frontend focused18/18 plus typecheck passed. Source/diff review accepted.
- Authenticated live Chrome on production: selected a public repo and prepared form. All4 needs and3 participation methods present. Feature showed current state/outcome immediately after need with no Issue field. Bug showed existing/new Issue choice and explicit capped list loader.
- Clicked Issue load: GitHub read completed; sample public repo had no open Issues, and empty state correctly offered new Issue or refresh. Switched to new-Issue option and PR method; informational creation text appeared without creating an Issue.
- Switched to a private repo and prepared form. Previous bug and PR choices were cleared. Only teammate/contributor/feature and application/automatic remained; no bug, PR or Issue chooser. Exercised contributor+automatic, feature+application, teammate+application. Feature kept descriptions without Issue. Automatic showed existing protection requirements.
- Desktop screenshot reviewed for field layout, labels and spacing. No publication, GitHub Issue creation, collaborator invite or PR merge performed. Nonempty50-item selection and malformed/PR/private response limits are isolated-test/source evidence, not a400-Issue live dataset test. Mobile viewport not tested.

Final documentation-only commit records this evidence; deployed application source remains379fe4f.
