# FIRST deployment checklist

Graph source of truth: `run.json`; this snapshot reflects ledger handoff.

- [x] `discovery` — Prepare FIRST-only host and deployment plan (done; owner `/root`)
- [x] `smtp-fix` — Bound email-change SMTP usage across varying destinations (done; owner `/root/review_backend`)
- [x] `smtp-review` — Independently review SMTP admission fix (done; owner `/root/security_verify`)
- [x] `smtp-verify` — Independently verify SMTP admission tests (done; owner `/root/security_verify`)
- [ ] `deploy-tooling` — Implement isolated FIRST deployment and backend-only send-machine (active; owner `/root`)
- [ ] `deploy-review` — Independently review deployment tooling before execution (draft; owner `/root/deploy_review`)
- [ ] `deploy-verify` — Independently verify deployment tooling checks (draft; owner `/root/deploy_verify`)
- [ ] `remote-deploy` — Deploy FIRST backend to the authorized host (draft; owner `/root`)
- [ ] `frontend-integration` — Connect existing FIRST Vercel frontend to live backend (draft; owner `/root`)
- [ ] `runtime-review` — Independently review deployed FIRST isolation and configuration (draft; owner `/root/deploy_review`)
- [ ] `runtime-verify` — Independently verify live FIRST auth integration (draft; owner `/root/deploy_verify`)
- [ ] `delivery` — Record accepted deployment and Git delivery (draft; owner `/root`)

No remote deployment or live service acceptance has yet been recorded. Update this summary when recording subsequent graph results.
