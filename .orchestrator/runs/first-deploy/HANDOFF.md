# FIRST deployment ledger handoff

Run and event history validated. Four nodes accepted: discovery, SMTP fix, independent SMTP review, independent SMTP verification. deploy-tooling is active under parent ownership. All downstream work remains draft. No new user approval blockers are introduced: remote deployment and backend-only send-machine were explicitly authorized. Runtime work is not claimed complete.

Independent deployment reviewer/verifier owner labels are planned roles (`/root/deploy_review`, `/root/deploy_verify`), not claims those agents have been dispatched. Set actual distinct owners before dispatch/record, and use actual agent identities in result files. Runtime verification can mutate only bounded FIRST test data. Review/verification agents must differ from implementation owner.

## Continue

Run from repository root:

```sh
node .orchestrator/bin/orchestrator.mjs status .orchestrator/runs/first-deploy/run.json
node .orchestrator/bin/orchestrator.mjs validate .orchestrator/runs/first-deploy/run.json
```

Edit the applicable `templates/<item-id>.json` with actual summary, checks, criterion evidence, agent identity and current completion timestamp; copy the completed draft under inputs with a fresh filename. Templates intentionally have blocked/not_verified placeholders and must not be recorded untouched. `pass` is valid only when every criterion is actually passed.

The deploy-tooling node is already active. After it has completed:

```sh
node .orchestrator/bin/orchestrator.mjs record .orchestrator/runs/first-deploy/run.json .orchestrator/runs/first-deploy/inputs/deploy-tooling.json --actor manager
node .orchestrator/bin/orchestrator.mjs sync .orchestrator/runs/first-deploy/run.json --actor manager
```

For each ready subsequent node, use native CLI transitions and result recording:

```sh
node .orchestrator/bin/orchestrator.mjs transition .orchestrator/runs/first-deploy/run.json deploy-review active --reason "Independent deployment review assigned" --actor manager
node .orchestrator/bin/orchestrator.mjs record .orchestrator/runs/first-deploy/run.json .orchestrator/runs/first-deploy/inputs/deploy-review.json --actor manager
node .orchestrator/bin/orchestrator.mjs sync .orchestrator/runs/first-deploy/run.json --actor manager
```

Replace node/result filename with the actual ready task. Never overwrite accepted results or events; rejected implementation requires a revision node. Keep credential/IP values out of all evidence. Reported evidence artifacts outside a work item's write scope should use `path: null` with a safe reference in description/acceptance; do not invent write ownership just to pass validation.

Deploy acceptance should establish SMTP configuration from actual evidence. If real SMTP cannot be completed, record actual blocked/not_verified criteria rather than accepting a live auth claim. Backend deployment can still be evaluated separately when its own criteria pass.

SMTP regression evidence uses fake Redis, SQLite and memory email only. Real Redis Lua concurrency/TTL, PostgreSQL locks and live delivery remain runtime checks. Independent reviewer recommends documenting the new request budgets in the API contract.

Root alone owns final commit/push. No ledger subagent push or deployment was performed.
