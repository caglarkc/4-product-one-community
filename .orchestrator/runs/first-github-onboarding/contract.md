# GitHub login with selected repository setup

User requests repository permissions at GitHub login/link, not as two later buttons. Preserve separate login OAuth and selected-repo GitHub App grants internally. Existing App permissions unchanged; never broaden OAuth to all repos.

- Successful login/link/signup (including email completion) enters `/github-kurulum` with fixed allowlisted next path. Setup checks existing linked identity, grant and authorized repositories; existing valid setup skips consent.
- Missing grant starts App OAuth once. App start accepts optional return_to choice `/`, `/hesap`, `/projelerim/yeni`, defaults last; stores in bound OAuth state and callback returns it. Frontend validates again.
- Connected grant but empty list goes to selected-repo installation choice. Existing GitHub setup URL `/projelerim/yeni?github_setup=1` redirects to onboarding. Return with no selectable repos stops with explanation/retry, never infinite redirects. Setup/manage state preserved only for fixed destinations, no secrets in URLs/storage.
- Cancel or failure preserves FIRST session and shows explicit retry; never auto-loop. OAuth callback status/installation IDs are not proof of repository access; GitHub user/installation/repo identity/admin checks remain authoritative.
- App authorization and own repo inventory require authenticated GitHub-linked user, not verified FIRST email. Preview/create/publication retain email verification.
- Project editor displays authorized repo dropdown and optional one manage action; incomplete older connections show one completion action. No separate connect+permission buttons.
- No new provider credentials, broad scopes or App settings changes. Automatic navigation does not grant consent for the user. Live consent still user-approved where platform requires.
- Backend/frontend disjoint writers; independent review and verification; root docs/push/remote Docker.
