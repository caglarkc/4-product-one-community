# H regression

Task h-regression; files FIRST/backend/** and FIRST/frontend/**. Manager execution against frozen G source.

## `.venv/bin/python manage.py test accounts --settings=config.test_settings --verbosity 1` in `FIRST/backend`

Exit: 0

```text
Creating test database for alias 'default'...
.................................................................
----------------------------------------------------------------------
Ran 65 tests in 1.047s

OK
Destroying test database for alias 'default'...
Found 65 test(s).
System check identified no issues (0 silenced).

```
## `.venv/bin/python manage.py check --settings=config.test_settings` in `FIRST/backend`

Exit: 0

```text
System check identified no issues (0 silenced).

```
## `.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.test_settings` in `FIRST/backend`

Exit: 0

```text
No changes detected

```
## `npm test` in `FIRST/frontend`

Exit: 0

```text

> first-web@0.1.0 test
> vitest run


 RUN  v4.1.11 /Users/caglarkc/Desktop/GitHub/4-product-one-community/FIRST/frontend


 Test Files  5 passed (5)
      Tests  61 passed (61)
   Start at  17:44:03
   Duration  1.61s (transform 272ms, setup 546ms, import 368ms, tests 1.51s, environment 2.72s)


```
## `npm run lint` in `FIRST/frontend`

Exit: 0

```text

> first-web@0.1.0 lint
> eslint .


```
## `npm run typecheck` in `FIRST/frontend`

Exit: 0

```text

> first-web@0.1.0 typecheck
> tsc --noEmit


```
## `npm run build` in `FIRST/frontend`

Exit: 0

```text

> first-web@0.1.0 build
> next build --webpack

▲ Next.js 16.3.5 (webpack)
✓ Running next.config.ts took 62ms

  Creating an optimized production build ...
✓ Compiled successfully in 955ms
  Running TypeScript ...
  Finished TypeScript in 1031ms ...
  Collecting page data using 9 workers ...
  Generating static pages using 9 workers (0/9) ...
  Generating static pages using 9 workers (2/9) 
  Generating static pages using 9 workers (4/9) 
  Generating static pages using 9 workers (6/9) 
✓ Generating static pages using 9 workers (9/9) in 164ms
  Finalizing page optimization ...
  Collecting build traces ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ƒ /api/auth/[...path]
├ ƒ /eposta-dogrula
├ ○ /giris
├ ○ /hesap
├ ○ /kayit
├ ƒ /sifre-sifirla
└ ○ /sifremi-unuttum


○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand


```
## `git diff --check` in `.`

Exit: 0

```text

```

Not performed: PostgreSQL/Redis/SMTP runtime, listening services, browser E2E/deploy (user scope exclusions); not_verified. Combined source contract integration is independently reviewed in H gates.

Manager source inspection: api.ts fetches csrf before all body-bearing POST/PATCH/DELETE requests; recovery-forms maps uid/token/key and refreshes me after verification; AccountStatus fields match ProfileSerializer, displays unverified email/phone, and redirects after current/all revocation. accounts/urls.py and Next route paths align including trailing slash. Full independent security and verification follow.
