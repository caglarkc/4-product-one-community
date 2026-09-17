# Deployment tooling / review evidence

Retrospective record of iterative preflight work. No live deployment result is established by this note.

Parent implemented backend-only send-machine (28 allowlisted files), strict SSH with sensitive configuration on stdin, release flock, isolated named/label-checked resources, selected loopback 18081, DB/Redis readiness and connection checks, migrations, pre-upgrade database dump and prior image/environment rollback. Database migrations are not automatically reversed.

Independent security_verify initially required corrections: first-install readlink detection; config mutation outside flock; existing container/volume/network ownership; real DB/Redis connectivity checks; environment restoration on existing-deployment failures plus image rollback; dotenv backslash handling. Follow-up also required allowing a retry only when the existing backend binding belongs to FIRST. Parent applied fixes, including rejecting a trailing backslash explicitly.

Final security_verify review: PASS for scoped static preflight; no remaining blocker identified. Real Compose execution, SMTP credentials and recovery behavior still require runtime evidence. Reviewer made no code edits or remote calls.

Independent commands reported by security_verify:
- bash -n FIRST/backend/deploy/release.sh: exit 0.
- python3 send-machine --dry-run: exit 0; exactly 28 allowed backend files, no env/frontend/tests/venv/Git/other products.
- Python ast.parse for send-machine and FIRST/backend/deploy/configure.py: passed.

Ledger agent separately repeated AST parsing, bash -n and ./send-machine --dry-run successfully, without launching services.

Parent reports user-authorized copying of only five SMTP configuration fields from existing backend configuration into FIRST shared .env, mode 600. Values remained hidden; no mail was sent. Existing source application was not changed. This is configuration preparation, not successful SMTP delivery evidence.
