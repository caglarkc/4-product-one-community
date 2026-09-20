# FIRST project taxonomy delivery — 20 September 2026

## Implemented

25 project types, 394 type-specific purpose categories and six development stages. Canonical catalog: `FIRST/backend/projects/taxonomy.py`; full readable list: `FIRST/proje-kategorileri.md`. API contract: `FIRST/contracts/project-api.md`.

Backend requires all three choices on create, validates parent/child membership, and validates merged partial updates under the current project row lock. Archive-only updates preserve classification. API returns catalog labels. Frontend uses API options and labels, resets child/consent on parent change, shows stage descriptions and field errors, and distinguishes development stage from sharing status. Legacy config disables submission with retry; legacy labels show Belirtilmedi.

## Review and verification

Catalog, backend and frontend were delegated to bounded writers. Independent reviewer accepted the whole source diff with no P0/P1/P2 findings. Manager inspected final source/diff and acceptance criteria. No tests, lint, typecheck, local build or browser/live user scenario were run, per repository preference. Actual visual appearance and authenticated create/edit workflows remain unverified at runtime.

## Schema authorization and backend delivery

User explicitly selected “Yalnız gerekli şema migration’ını uygula”. Application commit `5fd73e4d183418d8b7c2f4e9864e55121685fe65` was pushed to origin/main and remote hash matched. Existing `./send-machine` pulled that commit and deployed release `20260920T134328-5fd73e4d1834`.

`projects.0002_project_classification` applied successfully: only two AddField operations, no data migration/backfill. Standard deployment Django check found no issues, PostgreSQL/Redis connectivity passed, all three containers became healthy and health returned `{"status":"ok"}`. Persistent data and other projects preserved.

## Frontend delivery

GitHub Vercel status for application commit `5fd73e4` reported success: “Deployment has completed”. No manual frontend deployment was started.
