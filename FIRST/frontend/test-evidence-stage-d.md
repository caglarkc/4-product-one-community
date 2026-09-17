# D writer baseline / E gate input — 2026-09-17

Task: FIRST normal login/register web. Owned files: FIRST/frontend only. No backend/contracts/orchestrator/Git writes. This is implementer evidence; independent E review/verification belongs to parent run nodes.

| Attempt | Command / scope | Result and evidence |
|---|---|---|
| 1 | `npm view next version && npm view react version` restricted shell | FAILED: registry DNS ENOTFOUND; no dependency state changed. Tool session 49068, final chunk 0b99b2. |
| 2 | Same npm query, approved elevated network | PASS: Next 16.3.5, React 19.3.0. Chunk 4b462c. |
| 3 | `npm install --save-exact && npm install --save-dev --save-exact typescript @types/react @types/react-dom @types/node eslint eslint-config-next@16.3.5 vitest @vitejs/plugin-react @testing-library/react @testing-library/user-event @testing-library/jest-dom jsdom` in frontend | PASS: 445 packages audited, zero vulnerabilities. Tool session 35204 / 22b076. Registry emitted eslint 9.39.5 support warning; pinned Next eslint config currently resolves this version. |
| 4 | `npm test && npm run lint && npm run typecheck && npm run build` accidentally from repo root | FAILED: ENOENT root package.json; no tests executed. Chunk 078b44. Corrected cwd below. |
| 5 | Same check chain in FIRST/frontend | PASS: 3 test files, 20 tests; eslint exit 0; tsc exit 0; Next webpack build exit 0. Chunks 865ae4 and f3b627 / session 21244. Vite emitted CommonJS config future-compatibility warning; fixed via package `type: module`. Next added generated dev types include to tsconfig. |
| 6 | Same check chain after ESM config + password error/helper accessibility correction | PASS: 3 files, 20 tests, 1.13s; eslint exit 0; tsc exit 0; production webpack build exit 0. Chunk 5445e1 / session 47516. Routes `/`, `/giris`, `/kayit`, `/hesap` static; `/api/auth/[...path]` dynamic. |

Tests: `tests/forms.test.tsx` (7), `tests/api.test.ts` (5), `tests/proxy.test.ts` (8). Cover exact register/login fields, remember_me boolean, success navigation, error/field rendering, pending/duplicate prevention, CSRF rejection without credential submission, anonymous/me state, unverified reminder; fresh CSRF per mutation, credentials/no-store; fixed origin and invalid config, trailing slash, multiple Set-Cookie preservation, cookie/Origin/Referer/CSRF forwarding, traversal rejection, upstream redirect rejection. Test fetch responses are confined to tests.

Technical choices: Route handler proxy (Node fetch) rather than opaque rewrite makes explicit cookie/header/no-store/redirect/error handling testable in process. Fixed backend origin is server-only; no dynamic Host target. `skipTrailingSlashRedirect` retains Django routes. `next build --webpack` avoids launching a runtime or preview service. Minimal native controls/common CSS follows current frontend skill. `/hesap` truthfully marks profile/home as next-stage work; no invented finished features.

Not run / not_verified: listening backend/frontend, browser E2E/responsive rendering, actual PostgreSQL/Redis/SMTP, real HTTPS/cookie proxy delivery, deployment and trusted client IP forwarding. User prohibits runtime servers and live services. Code/build checks do not establish live system operation. Backend IP budget currently aggregates proxy egress until separately configured trusted ingress; no arbitrary forwarded client IP is accepted here.

## E failed gate and revision (retained)

Parent reported E gate FAILED: raw HTML username length limits disagreed with backend NFC semantics (60 raw code points may compose to 30 accepted characters); logout control coverage was missing; per-client rate-limit identity needed explicit proxy integration. These findings were not marked passed by baseline tests.

Correction files: `src/components/auth-form.tsx` removes raw min/max length for username and NFC-normalizes payload, leaving canonical length enforcement to Django; `src/components/account-status.tsx` uses synchronous ref lock for logout; `src/lib/backend-proxy.ts` adds optional HMAC IP assertions with paired server-only config, >=32-character shared key and single valid IP validation; env/README record trust setup and runtime limitations. No F/G feature work.

| Attempt | Command / scope | Result and evidence |
|---|---|---|
| 7 | Check chain mistakenly invoked from repository root | FAILED ENOENT root package.json; no checks ran (chunk 91a6e6). |
| 8 | `npm test && npm run lint && npm run typecheck && npm run build` in FIRST/frontend | PASS: 35 tests across 3 files (1.41s), eslint 0, tsc 0, webpack production build 0. Session 78607 / chunks 3c4e5c and final completion. |

New regression coverage: userEvent typing 60 raw username code points sends 30 NFC characters; logout success, failure retaining user/retry, pending/double-click; correct HMAC signed method/path/timestamp/IPv6, secret/header pair validation, missing/malformed/multiple/scoped IP rejection, incoming assertion spoof ignored in disabled mode. Test-only shared key is synthetic. All prior not_verified runtime boundaries remain unchanged. Independent rereview/verification is owned by parent.
