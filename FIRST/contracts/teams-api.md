# FIRST independent teams API

Approved 25 September 2026. Implementation tracked in `first-release-completion`; this contract is not runtime verification.
Base: `/api/auth/teams/`. Existing Bearer session/CSRF and strict serializer rules apply.

## Policy

One owner, admins and members. Only owner appoints admins, transfers ownership or closes team. Owner/admin edits profile/recruiting and manages ordinary member applications/invitations. Admin cannot remove owner/admin. Ownership transfers to an existing active member before owner can leave; a sole owner may close. Any ordinary member/admin may leave. Closing soft-deactivates team and detaches projects, never deletes GitHub data. Teams and projects independent: creating a team needs no repo or GitHub account; authenticated verified email is required for mutations. Invitations respect target invitations_open and active status. Team membership never creates GitHub access.

A project may belong to one team through a unique team/project association. Attach requires actor is project's owner and team owner/admin. Detach allowed to project owner or team owner/admin. Public team detail exposes only projects independently visible to caller; team membership confers no project visibility. Inactive owners/teams are unavailable publicly; do not leak selected-only projects through counts. Account deletion must not orphan an active team; integration supplies transfer/close guard.

## Endpoints

- GET ``: paged discovery (`q`, `recruiting=1` optional); `{teams,count,next_page,previous_page}`.
- POST ``: `{name,description,recruiting,recruitment_text,skills,organization_url}`; `{team}` 201. GitHub organization URL is optional external link only, not verified membership/sync.
- GET `mine/`: `{teams}` memberships, plus pending received invitations in `{invitations}`.
- GET `<uuid>/`: `{team,members,projects,requests,my_request}`. Requests visible only manager or involved requester; public member fields username/full_name/role only.
- PATCH `<uuid>/`: editable profile/recruiting fields; `{team}`.
- DELETE `<uuid>/`: owner closes team; `{closed:true}`.
- POST `<uuid>/apply/`: `{explanation}`; create/reopen pending membership application if recruiting; `{request}`.
- POST `<uuid>/invitations/`: `{username}`; `{request}`.
- POST `<uuid>/requests/<uuid>/action/`: `{action:'accept'|'reject'|'withdraw'|'decline'}`. Managers decide applications, invite recipient decides invitation, applicant may withdraw. Serialize conflicting changes; membership created only on accepted request.
- POST `<uuid>/members/<username>/role/`: `{role:'admin'|'member'}` owner only.
- DELETE `<uuid>/members/<username>/`: remove ordinary member (owner may remove admin); self uses leave.
- POST `<uuid>/transfer/`: `{username}` existing member; old owner becomes admin.
- POST `<uuid>/leave/`: `{}`; owner prohibited.
- POST `<uuid>/projects/`: `{project_id}` attach.
- DELETE `<uuid>/projects/<uuid>/`: detach.
- PUT/DELETE `<uuid>/bookmark/`: save/remove saved team, no access granted.
- GET `bookmarks/`: paginated `{teams,count,next_page,previous_page}` active teams only.

Team shape: `id,name,description,recruiting,recruitment_text,skills,organization_url,owner_username,my_role,is_active,saved,created_at,updated_at`. Request shape: `id,team_id,team_name,username,kind,status,explanation,created_at`.

All input sizes bounded. Skills from existing curated catalog; no arbitrary permission values. Row locks serialize roles, transfer, memberships and unique project attachments. No external notifications/messages. Separate FIRST team requests UI provides pending invitation visibility.

All collections use 12 rows per page. Mine accepts `page` and `invitations_page`, returns `team_pagination` and `invitation_pagination`. Detail accepts `members_page`, `requests_page`, `projects_page`, returns `member_pagination`, `request_pagination`, `project_pagination`. Each metadata object is `{count,next_page,previous_page}`. Manager request lists contain pending requests only; `my_request` preserves own latest status. Project visibility is filtered before counts/pagination. Public reads are throttled. Project detail exposes active team `{id,name}` only while its owner is active.
