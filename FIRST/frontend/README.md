# FIRST web

Next.js / React / TypeScript frontend. Auth, OAuth exchanges, sessions, account and repository operations run in Django. Browser requests go directly to `https://167.235.158.118/api/auth/`; there are no Next API proxy route handlers or frontend server secrets.

Actual `.env.production` and local `.env.local` use `NEXT_PUBLIC_API_URL=https://167.235.158.118`. Vercel builds after Git push; no manual deployment is required. The public origin is embedded during build. Existing unused Vercel proxy environment variables have no consumer.

The shared `src/lib/api.ts` sends opaque Django Redis session keys as Bearer credentials with `credentials: omit`. Browser localStorage preserves the session across OAuth navigation and tabs. Session authority, expiry, rotation and revocation remain backend responsibilities. Browser script access to storage makes XSS prevention important; provider tokens and backend secrets never enter browser storage. Old cookie sessions require a fresh login.

Before mutations the client retrieves a session-bound CSRF token. Expired sessions clear storage; bootstrap retries once. Requests serialize within a tab and session header updates compare the request's original token to avoid overwriting a newer session. Callback pages forward only bounded code/state/error parameters to Django, scrub the address bar and follow fixed backend `redirect_to` values. Provider callback registrations remain unchanged.

Backend CORS allows the exact frontend origin and the explicitly configured local origin. Native clients use the same Bearer API and CSRF bootstrap with the configured FIRST Origin header. nginx terminates the existing IP TLS certificate; Docker binds only loopback. See [API contract](../contracts/auth-api.md) and [deployment](../deployment.md).

Review for this revision is source-only. No tests, lint, typecheck, browser scenarios or extra local production build were run, per owner instruction. Earlier test evidence documents describe earlier implementations.

## Shared FIRST design language

[FIRST design language](../tasarim-dili.md) is the visual contract for all current and future screens. The current dark graphite, blue-link and green-action palette is implemented in `src/app/tokens.css`. That file owns semantic colors, typography, spacing, radii, focus and control sizes; `src/app/globals.css` consumes them for shared controls and responsive layouts.

Use the typed primitives in `src/components/ui/index.tsx`: `Button`, `ActionLink`, `Field`, `Input`, `Select`, `Checkbox`, `Alert`, `Surface`, and `PageHeading`. Button and action-link variants share one CSS definition. `Button` defaults to `type="button"`; form submission must explicitly use `type="submit"`. Native attributes remain available and loading disables buttons. Give `Field` and its control the same unique ID and connect help/errors with `aria-describedby`; the auth and account forms demonstrate this pattern. Keep navigation as links and provide `role="alert"` / `role="status"` only for relevant feedback, not every decorative surface.

Pages combine these primitives and layout classes instead of defining their own colors or copies of buttons. The account layout uses two columns on larger screens and preserves reading order in one column on small screens. Account, OAuth, project discovery/editor/detail, participation and notification screens use this system. The participation API is documented in [participation-api.md](../contracts/participation-api.md).

18 September 2026 implementation checks: production build, lint and typecheck passed; component/API/proxy suite passed (64 tests, including shared-control behavior). These are local code checks; production deployment, real email delivery and real-user account changes are not verified by this design task. Browser appearance and interaction checks are recorded separately by the integrating reviewer.

## Listing participation integration — 21 September 2026

The editor selects a single need and immutable participation method, visibility, application availability and feature/bug Issue requirements. The home feed filters taxonomy, need and participation method. Project detail exposes application, distinct viewer/invitation controls, Issue retry and explicit GitHub collaboration refresh. `/basvurular` manages applications/invitations and reviewed-SHA PR decisions; `/bildirimler` displays site notifications. FIRST acceptance and GitHub invitation acceptance are separate states. Contributor statistics and chat remain deferred.

For this run the user explicitly requested tests and live site verification. Current evidence and any limits are recorded in [the integration run](../../.orchestrator/runs/first-listing-participation/run.json), superseding the historical source-only notes for this change.
