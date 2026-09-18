# FIRST project sharing — implementation contract

Current phase: own project list, create/edit/archive + public share detail. No application/invite workflow and no file browsing. Email verified + linked GitHub required to create. Phone ignored. One active sharing per repository globally. Category options supplied by backend (initial software/design/research/documentation/other, pending user answer). Shared content consists of user title/category/description + plain README excerpt max 3 sentences/600 chars. Private project DTO excludes repo URL/full_name/id/owner and all files; owner management repo selection may see their own repo identifiers. Public project DTO includes canonical GitHub repo URL/full_name only after live visibility/access validation. Fail closed on GitHub access revocation or unknown privacy; don't expose stale README/link publicly.

Transport uses existing signed JSON gateway `/api/auth/` (resource urls below relative to it), existing `api()` helper/CSRF/AuthView. Backend Django app `projects`; include its URLs in accounts urls under `projects/`. Backend writer owns accounts/urls.py addition. Existing Google/GitHub OAuth unchanged. No frontend client secrets.

GET projects/config -> {categories:[{value,label}],github_app_enabled:boolean}
GET projects/mine -> {projects: Project[]}
GET projects/github/status -> {enabled:boolean,connected:boolean,github_linked:boolean,installation_url:string|null}
POST projects/github/start {} -> {authorization_url:string} separate App OAuth, state bound to current session/user/linked UID/security_version + PKCE; exact server callback URI.
GET projects/github/callback?code&state -> {status:'connected'}; Next route `/github-repo/callback` redirects to `/projelerim/yeni?github=connected|failed` and forwards cookies. Proxy query allowlist add projects/github/callback (code,state,error), no install callback query authorization.
GET projects/github/repositories -> {repositories: Repository[]}; authenticated linked App user, paginated internally with safe bound/error not silent truncation; verify /user ID equals linked social UID, installation App ID, current install selection and permissions.admin true. Empty list valid and installation_url lets user choose additional repo(s).
POST projects/github/preview {installation_id:number,repository_id:number} -> {repository:Repository,readme_excerpt:string}; live authorization, README plain text no links/images/code/html and bounded download.
GET projects/<uuid> -> {project:Project}; shared public page (unauth allowed), active records only for others. Fresh provider visibility; do not return private identifiers.
POST projects {installation_id,repository_id,title,category,description,readme_excerpt} -> {project:Project} status201. Excerpt must equal server preview/current safely derived excerpt or empty, not arbitrary private contents. Explicit confirmation UI before sharing. Repository identity/privacy server authoritative.
PATCH projects/<uuid> {title,category,description,is_active} -> {project:Project}; owner only, live repo management proof for edits/reactivation; archive available even disconnected. Disallow repo identity changes. One active per repo DB constraint incl race.
Project = {id:string,title:string,category:string,description:string,readme_excerpt:string,is_private:boolean,repository_url:string|null,repository_name:string|null,is_active:boolean,created_at:string,updated_at:string}
Repository = {id:number,installation_id:number,full_name:string,name:string,private:boolean,description:string,html_url:string}; owner-only data, no token.

Errors: existing detail/errors shape; status401/403 login/verified email/github required, 409 duplicate active repo, 503 provider/config unavailable; code strings actionable. List mine works when provider disabled; show own stored preview but safest no stale public external link without current visibility verification.

App OAuth: expiring user tokens + refresh encrypted at rest via dedicated Fernet key. No installation JWT/private key needed for this phase: App user token intersects App selected repos and user's permissions. App ID/config validates intended App's installations. Fixed GitHub API hosts/paths; no client URLs fetched. Refresh serializes/locks credential so rotating refresh race doesn't lose token. Revoked/expired credentials force reconnect; no secret provider responses logged.

Config keys: GITHUB_APP_ENABLED, GITHUB_APP_ID, GITHUB_APP_SLUG, GITHUB_APP_CLIENT_ID, GITHUB_APP_CLIENT_SECRET, GITHUB_APP_REDIRECT_URI=https://first.alicaglarkocer.com/github-repo/callback, GITHUB_APP_TOKEN_KEY (Fernet). Setup URL https://first.alicaglarkocer.com/projelerim/yeni?github_setup=1; setup query never trusted as proof. OAuth login `user:email` remains unchanged.
