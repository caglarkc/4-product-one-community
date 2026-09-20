# FIRST listing participation — delivery

## Delivered

Backend and frontend integration committed and pushed to main: `d6b7e5c`, `308a614bc24ac93eb1c0a051582cc324d8fd1790`.
Backend release: `20260920T212838-308a614bc24a`. Remote checkout pulled the matching commit; Docker build and migration0004 succeeded. Backend, PostgreSQL and Redis healthy; health endpoint returned ok. Vercel reported successful deployment of the same code commit.

Live site: https://first.alicaglarkocer.com

## Verification

- Backend: 202 tests passed; migration drift absent; Django checks passed.
- Frontend: 123 tests in 12 files passed; typecheck passed; lint 0 errors and one existing ref-cleanup warning.
- Independent source review found no remaining blockers.
- Live HTTPS API: public feed/config/valid filters 200; invalid need 400; unauthenticated participation and notifications 401; deleted original test detail 404.
- Signed-in live Chrome: discovery filters, applications dashboard, notifications page and full listing editor loaded.
- Created temporary application-mode teammate listing using the original public test repo, link-only visibility and no README sharing. Detail displayed correct category, need, participation and visibility.
- Live GitHub collaboration read succeeded and displayed no open PRs.
- Edit form kept need and participation method disabled. Changed visibility to selected-only and closed applications; saved detail showed invitation-only participation.
- Anonymous link-only detail returned 200 while discovery count remained zero. After selected-only save, anonymous detail returned 404.
- Removed only the user-authorized original test listing and the exact temporary live fixture, with owner/repo/title identity assertions. Remaining listing count zero; GitHub repository content unchanged.

## Active behavior and boundaries

Four need types, three participation modes, discovery filters, selected viewers, separate participant invitations, application decisions, notifications, Issue and PR integration are active. Automatic collaborator access fails closed unless actual GitHub protections satisfy the configured safety checks; no GitHub protection settings are modified automatically.

Actual collaborator invitations, Issue creation and PR merges were covered with mocked provider tests, not performed against a live repository. No second-account end-to-end invitation acceptance, private-repo live mutation, PostgreSQL concurrency stress or mobile viewport test was performed. Contributor statistics and chat remain deferred as agreed.

The final delivery commit records documentation/run evidence only; deployed application source is 308a614.
