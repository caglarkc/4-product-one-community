# FIRST account reset controls

User explicitly requests test-stage identity disconnect, separate repository permission disconnect and account deletion. Supersedes previous no-disconnect decision for GitHub only.

- POST `/api/auth/github/disconnect/`, confirmation `GITHUB`: recent authentication, another login method required; revoke repo grant, remove credential and GitHub identity, archive shares.
- POST `/api/auth/projects/github/disconnect/`, confirmation `REPO`: recent authentication; revoke GitHub App user grant, remove credential, archive shares; keep GitHub identity/login.
- DELETE `/api/auth/account/`, confirmation `HESABIMI SIL`: recent authentication, revoke stored App grant, cascade FIRST user data and shares, invalidate sessions, logout.
- Disconnect responses include detail/user; deletion detail. Existing CSRF and error/reauthentication contracts apply. Status adds credential_stored for expired credential cleanup.
- Disconnect invalidates other sessions and pending provider flows while preserving current session. Serialize mutations against callbacks and project publication. Provider revocation is best effort: expired/revoked credentials or outages must not trap local account data. Known provider failures still clear local data; return github_cleanup_required=true and explicit warning to revoke remaining permission in GitHub settings. Successful revoke returns github_authorization_revoked=true; no stored credential yields null. Confirmations explain this before action, deletion redirect shows cleanup warning.
- GitHub repositories/accounts are never deleted. GitHub App installations remain; user grant removed. Login OAuth token was never stored, so FIRST unlink cannot revoke that separate GitHub consent; expose GitHub settings link and explain.
- GitHub-only accounts can create a password through existing verified-email recovery before sensitive actions; no test auth bypass.
- Confirm each action; typed confirmation for full deletion. Do not delete the real account during browser verification. Automated fixtures may exercise deletion.
- Backend and frontend writers have disjoint scopes. Root owns docs, graph, integration, push and existing remote deployment.
