# FIRST community discovery and redesign

User explicitly requests everyone’s shared projects on home and a complete modern GitHub/developer-inspired visual revision. New dark graphite direction supersedes prior warm palette; FIRST/tasarim-dili.md is updated under that authorization.

## Feed contract

GET /api/auth/projects/?page=N; default 1, positive integer; fixed 12 per page. Response projects, count, next_page, previous_page. Deterministic newest-created ordering with UUID tie break. Only active shares from active owners, regardless of requester. Public summary allowlist: id,title,description,category,subcategory,stage,category_label,subcategory_label,stage_label,created_at,updated_at. No repository identifiers/names/links/privacy, README, account or credential data. No GitHub call per card. Existing detail repository proof and consented preview remain unchanged. Feed rate limited separately. POST keeps existing requirements. No schema change.

## Frontend

Public feed not gated by session loading. Real count and pagination, empty/loading/error/retry. Shared repo-inspired cards on home/MyProjects; no fabricated social metrics. Dark theme across all existing shared surfaces/controls/navigation, full workflow preservation. Category hierarchy and stage readable. Shared tokens, system sans/mono, tiny native SVG, no dependencies. Preserve authentication, privacy confirmation, taxonomy validation, security and account behavior. Responsive and keyboard states reviewed in source only.

## Ownership and delivery

Backend writer: projects/views.py and urls.py. Frontend writer: relevant frontend/src files, no tests. Manager: product/design/API docs and run. Independent reviewer after both layers. Manager source verification and normal commit/push/backend deployment/Vercel status. No tests/lint/typecheck/local build/browser. Runtime scenario and visual fidelity explicitly unverified.
