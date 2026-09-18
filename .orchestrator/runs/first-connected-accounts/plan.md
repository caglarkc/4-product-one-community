# Connected provider profiles

User asks for account-page visibility of Google/GitHub connections, with GitHub
presented as a profile and Google as a linked account. No LinkedIn provider is
introduced. Preserve existing login/link/no-unlink decisions.

Backend owns FIRST/backend display metadata persistence, serialization, tests and
bounded public GitHub legacy enrichment command. Frontend owns FIRST/frontend
provider cards, shared styles and tests. Manager owns contracts/docs/run/deployment.
Independent read-only reviewer owns findings; manager runs verification.

User contract adds connected_accounts array (provider, display_name, username,
email, avatar_url, profile_url) while keeping providers list unchanged. Values are
minimal whitelist, scoped to current user. Missing legacy Google metadata must not
be represented using FIRST email. Provider tokens and raw payload never exposed.
Metadata must not influence account matching/ownership/security decisions.

Existing GitHub profile data can be enriched from public provider ID lookup after
ID validation; no external requests on account GET. Provider successful login/link
refreshes display metadata. Frontend handles missing images/data and only trusted
provider URLs, preserves Google no-link and Github existing link behavior.

Quality gates: backend/frontend tests, lint/typecheck (no local production build),
independent review, remote root pull/build/health and Vercel automatic deployment.
Verify account UI at desktop/mobile on live data after deployment.
