# H independent verification — PASS

Verifier: /root/contract_audit, separate from implementers and reviewer; no source writes. Files: FIRST/frontend account-status/account-form/recovery-forms/api/routes/tests; FIRST/backend/accounts endpoints/URL resolver and tests.

Commands from FIRST/frontend, each exit0: `npm test` (61/5files,2.32s), `npm run lint`, `npm run typecheck`, then sequential `npm run build` (9pages, expected auth/recovery routes). Commands from FIRST/backend, each exit0: `.venv/bin/python manage.py test accounts --settings=config.test_settings --verbosity 1` (65,1.950s); `.venv/bin/python manage.py check --settings=config.test_settings` clean; `.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.test_settings` nochange.

Additional `.venv/bin/python -` probe extracted frontend static API paths, added login/register/logout/CSRF and UUID session DELETE and resolved16 distinct frontend calls using Django URL resolver without networking. All matched. Evidence: native verifier final report in parent conversation; manager full command outputs h-regression.md.

Confirmed token link opening does not mutate; explicit reauth retry retains form; profile/reset/key/password payload alignment; session deletion/revocation redirects;401/403/429/503/invalid token/field error coverage; fresh CSRF, cookie/no-store/fixedproxy contract.

Not performed: actual PostgreSQL/Redis/SMTP, trusted ingress transport, deployed HTTPS/cookie browser behavior, visual/responsive browser control, E2E and deploy — not_verified per user scope. Test success is not live verification.
