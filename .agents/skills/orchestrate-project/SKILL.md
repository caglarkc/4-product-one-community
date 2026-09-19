---
name: orchestrate-project
description: Orchestrate complex repository work with dynamic task decomposition, dependency graphs, risk-based independent review and verification, native subagent/worktree use when available, portable handoffs when unavailable, and resumable run history. Use for project-manager, multi-agent, cross-layer, long-running, interrupted, high-risk, or multi-platform Codex/Cursor/Claude Code work; do not use for a single obvious low-risk edit.
---

# Orchestrate Project

Coordinate work through the vendor-neutral contracts in `.orchestrator/`. Keep the main agent responsible for scope, decisions, scheduling, acceptance, and final synthesis; delegate only bounded work that benefits from isolation or parallelism.

All four products use this one root system. Read `.agent/skills/cross/product-boundaries/SKILL.md` for product scope and `.cursor/maps/stack-shared-ai/technology.md` before assuming a stack. Set `policy.requiresIntegration: true` for shared or cross-product work.

## Start

1. Read `AGENTS.md`, `.orchestrator/SYSTEM.md`, and `.orchestrator/config.json`.
2. Run `node .orchestrator/bin/orchestrator.mjs discover` to refresh the skill, map, adapter, and repository catalog.
3. Inspect `.orchestrator/catalog/repo-context.json`. If maps are stale, treat them as hints and verify paths from source. Do not regenerate maps without respecting repo approval and install rules.
4. Create a run with `node .orchestrator/bin/orchestrator.mjs new --id <run-id> --title "<title>" --goal "<goal>"`.
5. Decompose the goal into work items in the generated `run.json`, then validate it.

## Decompose Dynamically

- Derive domains, capabilities, roles, and work-item `kind` values from the task; never select agents from a fixed roster merely because they exist.
- Give every item one objective, one responsibility boundary, explicit inputs, explicit outputs, acceptance criteria, read/write scope, dependencies, risk, and execution policy.
- Represent implement, review, test, verify, revision, integration, migration, documentation, and newly discovered work as graph nodes, not lifecycle states.
- Use only the generic lifecycle states defined by the contract. Add a revision node with `relations.revises`; never erase or relabel a failed attempt.
- Add discovery or specification nodes before implementation when product, data retention, API, security, or architecture facts are missing. Stop for user input when the missing decision is critical.

## Select Execution

- Keep tiny, obvious, low-risk changes inline.
- Delegate read-heavy exploration, noisy checks, independent review, or clearly separated implementation scopes.
- Parallelize only dependency-ready items whose `writeScopes` do not overlap. Use the batches returned by the `status` command.
- Prefer native subagents and native worktrees when the active platform supports them. Read the selected adapter under `.orchestrator/adapters/` before dispatch.
- If a native capability is absent, render a paste-ready handoff with `render`; do not pretend an agent, worktree, approval, or tool call occurred.
- Use worktree isolation for parallel writers when supported. If not supported, serialize writers or give them disjoint files.
- Keep approval decisions with the platform/user. Never weaken sandbox or permission settings to make a plan easier to execute.

## Default review scope

Follow `.agent/rules.md` control preference: write the code, then inspect source/diff. Do not write or run tests, lint/typecheck, smoke/E2E, browser or computer-use verification unless the user explicitly requests it for the task. Do not ask to run unsolicited tests. Propagate this boundary to all delegated agents. Review/verify nodes use source inspection by default; runtime behavior remains unverified. Existing deployment build/migration/health steps remain part of authorized delivery, without additional test passes.

## Apply Quality Gates

- For high or critical implementation, API contract, authentication, authorization, payment, data storage, migration, security, or deployment work, add an independent review node and a source-inspection verification node (not a test run).
- Give review and verify nodes `relations.reviews` or `relations.verifies`; use a different agent/thread where the platform permits it.
- Add an integration node for cross-layer runs and make it depend on accepted layer results.
- Record claims using `.orchestrator/contracts/result.schema.json`. A `pass` result requires evidence for every acceptance criterion and no failed check.
- Reject incomplete results, create a revision node, and preserve the original result and event trail.

## Operate and Resume

Use the CLI as the deterministic control plane:

```text
node .orchestrator/bin/orchestrator.mjs validate <run.json>
node .orchestrator/bin/orchestrator.mjs status <run.json>
node .orchestrator/bin/orchestrator.mjs sync <run.json> --actor manager
node .orchestrator/bin/orchestrator.mjs transition <run.json> <item-id> <status> --reason "<reason>" --actor <actor>
node .orchestrator/bin/orchestrator.mjs render <run.json> <item-id> --platform codex|cursor|claude-code
node .orchestrator/bin/orchestrator.mjs record <run.json> <result.json> --actor <actor>
```

Before resuming, run `status`, read the latest `events.jsonl` entries and stored results, then continue only ready items. Never infer completion from conversation memory alone.

## System maintenance

- Preserve the imported orchestration structure; this adaptation does not authorize system redesign. Propose a new reusable skill only when the same non-obvious workflow recurs or needs deterministic scripts/references.
- Propose a persistent custom agent only when a narrow role recurs and benefits from stable model/tool restrictions. Prefer ephemeral task agents otherwise.
- Update map/index inputs when source drift is confirmed; do not hand-edit generated maps as if they were source truth.
- Record architectural choices in the run `decisions` list. Update `.orchestrator/ARCHITECTURE.md` only for system-wide policy changes.
- Keep platform-specific syntax in adapters and keep the run contract vendor-neutral.

## Finish

1. Validate the run and all recorded result files.
2. Confirm required review, verification, and integration nodes are done.
3. For every completed task with file changes, follow `.agent/rules.md` Git delivery protocol: the integration-owning main agent creates meaningful Conventional Commits from accepted/task-owned changes and pushes to the current branch's verified upstream (or the same branch on origin). Do not ask again; honor explicit user exceptions. Subagents must not race independent pushes; force-push is forbidden. Verify the remote branch hash after push.
4. Record commit hashes/messages and the target remote/branch, or the explicit reason Git delivery was skipped.
5. Summarize accepted artifacts, unresolved risks, unrun checks, approvals still needed, and the exact next ready item.
6. Follow the repository's five-heading delivery format in `.agent/skills/meta/code-implementation-mode/SKILL.md`.
