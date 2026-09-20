# FIRST ilan / katılım API — 21 Eylül 2026

Base `/api/auth/projects/`; existing session + CSRF rules apply. Ordinary listing reads are DB-only. GitHub operations are explicit POST actions. Provider failures return 503 and durable record remains retryable; never imply GitHub invitation accepted merely because sent.

## Listing fields and configuration

`GET config/`: existing taxonomy plus `need_types`, `participation_modes`, `visibilities` arrays of `{value,label}`.
Need: `teammate|contributor|feature|bug`. Mode: `application|automatic|pr`. Visibility: `public|link|selected`.

Create uses existing preview and taxonomy fields plus required `need_type`, `participation_mode`, `visibility`; `applications_open` defaults true. Feature and bug require `current_state` and `desired_outcome`. Only bug requires exactly one of `issue_number` (positive integer, currently open Issue) or `create_issue:true`. Feature and other needs reject Issue selection/creation fields. Private + bug and private + pr are rejected. Bug creation also checks current GitHub repo privacy, not only stored preview privacy. Selected Issue is revalidated before the listing is persisted. Automatic mode requires live GitHub safety verification. Selected visibility accepts no self applications; owner invitations remain available. Closed listings must be `link` or `selected` (sending applications_open:false alone switches public to link).

PATCH detail accepts title/description/taxonomy/is_active plus `visibility`, `applications_open`, `current_state`, `desired_outcome`; need type and participation mode immutable. One active listing per repository remains enforced.

Project response adds need/mode/visibility and labels, applications_open, current_state, desired_outcome, issue_number (private hidden), issue_status, owner_username, is_owner, can_apply. Detail response is `{project, participation}`; `participation` is the current user's record or null (top-level, alongside project). Private repo identifiers/Issue data are only disclosed through explicitly refreshed collaboration endpoint after live caller access verification.

Unresolved bug Issue setup is excluded from discovery. Public feed `GET ?category=&subcategory=&stage=&need_type=&participation_mode=&page=` returns only active, public, open listings. Mine includes own archived/closed entries. Selected detail returns 404 unless owner, selected viewer, or explicitly invited participant. Applications alone do not retain visibility after selected restriction.

## Applications and invitation dashboard

Participation shape: `{id,project_id,project_title,username,kind,explanation,status,pr_number,pr_sha,decision,github_status,github_invitation_id,github_invitation_url,operation_state,operation_error,merged,created_at,updated_at}`. Private PR numbers and SHAs are not exposed in ordinary dashboard data. Kinds `application|automatic|pr|invitation`. Status `pending|invited|accepted|rejected|withdrawn|declined`. GitHub status `invited|active|missing` (empty before provider work). Operation state `idle|pending|failed|succeeded`. An operation pending/failed must be retried with the same decision, not replaced by rejection/withdrawal.

- `GET participation/`: `{sent:[],received:[]}`; received belongs to owned projects, sent to actor.
- `POST <id>/apply/`: `{explanation,pr_number?}`. Verified email and linked GitHub required. PR mode requires candidate-authored PR to exact repo. Automatic creates durable record then attempts access invite. Repeating returns same record; withdrawn/rejected records are not silently resubmitted.
- `POST <id>/invitations/`: owner `{username}` exact FIRST username. Sends a FIRST invitation, grants listing visibility but not GitHub access yet. Recipient must explicitly accept.
- `POST participation/<participation_id>/action/`: `{action:accept|accept_and_invite|reject|withdraw|decline|refresh, expected_sha?}`. Owner accepts applications, PR accept merges; accept_and_invite merges and invites. PR decisions require exact reviewed expected_sha. Recipient accepts/declines invitations; applicant withdraws pending application. `refresh` explicitly reconciles GitHub invitation/access (authorized owner or record user).
- Successful first acceptance emits site notification. Retrying same decision reconciles remote effects without duplicate entries. PR merge-only accepted status does not grant repository access.

## Selected viewers

- `GET <id>/viewers/`: owner `{viewers:[{username}]}`.
- `POST <id>/viewers/`: owner `{username}` gives listing visibility only.
- `DELETE <id>/viewers/`: owner `{username}` removes explicit visibility; an outstanding participation invitation independently allows listing visibility.

## Explicit collaboration refresh / issue setup

- `POST github/issues/` `{installation_id,repository_id}`: verified account and linked App credential required. The pair must match the owner's cached repo selection; current numeric repo identity and admin authorization are checked on GitHub. Private repositories fail closed. Response `{issues:[{number,title}],limit:50}` contains the newest 50 open actual Issues, with PRs excluded. One anonymous GitHub Search page (`repo:<verified-full-name> is:issue is:open`, sort created desc, per_page=50) prevents a full-repo scan and private-body disclosure; only number/title are returned. An empty list is valid. Incomplete/malformed results fail closed. Rate limit: 5 selector requests per actor per minute.

- `POST <id>/collaboration/` `{}`: visible listing required; private repositories additionally require live GitHub access by the caller. Returns `{pull_requests:[],issue:object|null,repository_url}`. Open PR and Issue provider fields are bounded. This is not an automatic feed fetch.
- `POST <id>/issue/` `{}`: owner retries bug Issue verification/creation. Create uses a stable project marker and persisted original creator GitHub UID; relinked identities cannot retry another identity's operation. Uncertain provider outcomes are reconciled. Result `{project}`. Issue creation persists the listing safely before the mutating provider call; if issue setup fails it returns project with issue_status pending/failed and setup_error; applications remain disabled until issue_status ready.

## Notifications

- `GET notifications/`: `{notifications:[{id,project_id,kind,message,is_read,created_at}]}` newest 100.
- `POST notifications/<id>/read/` `{}`: mark caller-owned notification read.

Site invitation acceptance sends GitHub invitation; UI must direct user to GitHub to accept it and then use refresh. No GitHub membership removal is implied by withdrawing FIRST applications, closing listings, or removing visibility.

PR stale-SHA or non-mergeable preflight returns 409 with `github_pull_changed` / `github_pull_not_mergeable`, operation reset to idle for a new reviewed decision. Unknown provider outcomes stay pending/failed with decision pinned. New invitations to archived listings are rejected; existing applications/invitations can still be processed (archive does not revoke existing invitations or GitHub access).

Feed response is a strict allowlist: existing id/title/description/taxonomy/labels/timestamps plus owner_username and need_type/need_type_label/participation_mode/participation_mode_label. The owner username is the public FIRST handle; email and other account data remain excluded. It does not include detailed requirement text, repository metadata, or Issue/PR identifiers.

Owner invitation can explicitly replace an idle pending/rejected/withdrawn/declined FIRST record, retaining its explanation/PR reference and recording the currently linked GitHub UID for the new invitation. It emits a new invitation notification and grants selected-listing visibility. A pending/failed external operation or successful membership cannot be replaced. Repeating the same outstanding invitation is idempotent.
