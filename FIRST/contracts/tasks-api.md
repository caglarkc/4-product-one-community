# FIRST general public Issue tasks

Approved 25 September 2026. Base `/api/auth/tasks/`. General tasks are independent of immutable listing need_type and participation_mode. Existing bug-listing Issue behavior remains unchanged.

Owner can attach an existing actual GitHub Issue or create one for a FIRST public project. No task assignment/reservation and no automatic refresh. Private tasks unsupported. Creation requires active verified user with linked selected-repository App, current repo admin and numeric identity. Public reads expose only public active, discoverable, application-open project listings with active owners; live GitHub privacy verification at task reads fails closed to avoid exposing cached public Issue text after privacy changes. Manual refresh uses anonymous GitHub read after owner authorization (no owner's credentials to read public Issue bodies), rejects PRs.

- GET `` with `q`, `state=open|closed|all`, `project_id`, `cursor`: `{tasks,next_cursor,has_more}`. Bounded signed-cursor database candidate windows, current provider public check cached only within request; transient provider failure returns unavailable, private/missing repo candidates are suppressed. No global counts or pre-verification text search metadata. Search and state filtering are applied only after public verification; next cursor means more candidates, not guaranteed matching results.
- GET `projects/<uuid>/`: visible public project task list plus owner's pending/failed creation records; `{tasks}`.
- POST `projects/<uuid>/`: attach `{issue_number}` OR create `{title,body,request_id}` UUID idempotency key; `{task}`. Owner only.
- POST `<uuid>/refresh/`: `{}` manual title/body/state sync, owner only; `{task}`.
- POST `<uuid>/retry/`: `{}` reconcile same durable pending creation via stable marker and author. Once a POST may have been attempted, retry is reconciliation-only; it never blindly creates again.
- DELETE `<uuid>/`: remove FIRST task link only; no GitHub Issue deletion/closure.

Task: `id,project_id,project_title,issue_number,title,body,state,issue_url,synced_at,operation_state,operation_error`. Unknown provider outcomes retained and retryable; don't claim success without provider identity match. Snapshot title/body max 200/10000 chars. Provider paging and request deadlines bounded; q length100, candidate window size12. Local state transitions under user/project/task locks in consistent order. No provider call causes local DB lock to hang unbounded. Record expected GitHub identity for create; logout/unlink invalidation respected. External Issue creation only on user's explicit form submission, never during verification.

Owner task responses also include `request_id` (null for attached existing Issues), allowing exact frontend reconciliation rather than title/body matching. A project has at most 50 FIRST task records including pending operations. The frontend preserves the exact create payload in tab sessionStorage before POST; unknown outcomes retain their key, and an explicit checked/discarded form can start a different task without deleting the backend reconciliation record.
