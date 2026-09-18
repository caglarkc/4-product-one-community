# FIRST GitHub integration

User authorized GitHub OAuth login/signup, existing account linking, push and remote
root SSH pull/rebuild. Also requested persistent FIRST delivery rules. Scope excludes
repository access and other products.

- Backend agent: FIRST/backend accounts/config/tests; no env or deploy changes.
- Frontend agent: FIRST/frontend; no production build.
- Manager: env, deployment script/config merge, API/docs, rules/skills, verification
  and Git/remote delivery.
- Independent reviewer: read-only deployment and auth review.

Contract follows Google JSON flow using github namespace. Callback externally at
/accounts/github/login/callback/. Verified primary email from GitHub /user/emails
may match an existing account; permanent GitHub ID owns later logins. New users
complete required profile without password. In-app linking binds the current user,
session and security version with recent independent reauthentication. No unlink.
GitHub OAuth cannot assert fresh password authentication: GitHub login does not
satisfy the sensitive-action recent-auth check. Existing password or linked Google
reauth is used; social-only users may establish a password through email recovery.
No repo scopes and no persistent provider tokens.

Deployment uses clean pushed main, remote clean checkout and git pull --ff-only,
exact commit archive, existing release.sh backups/build/migrations/health. Vercel
performs its configured automatic frontend build. Live verification must distinguish
endpoint checks from a completed real provider login.
