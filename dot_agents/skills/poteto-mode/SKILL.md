---
name: poteto-mode
description: Scoped engineering workflow with deliberate parallelism, artifact-based verification, and explicit stopping points. Use for /poteto-mode or requests to work in this style.
disable-model-invocation: true
---

# Working mode

Use the shortest workflow that delivers the requested outcome. Follow the [execution contract](../pstack-runtime/SKILL.md) for authority and verification; load its capability references only when needed. Existing project workflows own their concrete commands and checks.

## Principles

- Observe before assuming. Trace the relevant behavior and consult primary documentation when an API or library contract matters.
- Fix the responsible mechanism. Choose a useful data shape and boundary before adding guards or abstractions. Preserve unrelated behavior and local changes.
- Work in verifiable units. Establish acceptance checks before editing, and keep each completed unit reviewable. Commit boundaries and PR boundaries need not be identical.
- Parallelize independent work. Separate mutable state and review actual worker output. Keep coupled changes and repository-wide operations with one owner.
- Turn repeated corrections into focused checks or tooling rather than more mandatory prose. Search for an existing check before adding another.
- Stop when the requested outcome is verified. Report follow-up work without starting it automatically.

These rules are sufficient for ordinary tasks. The `principle-*` skills are optional reference material for a specific unresolved decision, not a reading checklist. Explain consequential choices, not which principles you read.

## Default workflow

1. Establish the outcome, non-goals, authorized actions, and smallest useful check. Inspect the current diff and relevant project instructions. Use a short checklist only when multiple steps need tracking.
2. Investigate enough to choose the responsible layer. Ask genuine product or preference questions with a recommendation. Use the installed `grilling` workflow when requested or when unresolved choices materially affect scope; do not ask the user to supply facts you can observe.
3. Implement within scope, reusing the project's patterns. Delegate independent slices when useful under the [delegation contract](../pstack-runtime/references/delegation.md). Compare alternative designs only when the choice is consequential and unsettled; ordinary changes do not require `architect` or `arena`.
4. Run the relevant checks and inspect the final diff. Distinguish passed, failed, unavailable, and blocked. Stop at the authorized stage; commit, PR, merge, and cleanup follow the user's request and existing project workflows.

For bug fixes, capture a reproduction or the strongest available evidence before editing. For refactors, run the same behavior checks before and after. For performance work, compare under matching conditions and reject changes that do not improve the intended measure.

## Review and verification

- Triage automated findings against the current code, expected behavior, and actual impact. Do not mechanically fix every warning or dismiss an issue solely because a bot reported it.
- Associate findings and checks with the revision and local changes they cover. Reassess affected evidence after a branch, base, or working-tree change.
- For UI or CLI changes, use existing project verification skills first. Check affected interactions and state transitions, not just initial rendering. Compare related views, empty or loading states, narrow layouts, localization, and keyboard behavior when the change touches them.
- If a correction exposes a shared mechanism, inspect related consumers. Fix only those covered by the task; report broader opportunities separately.
- Before publishing, match the PR description to the final diff and preserve any repository-managed content. Use the existing PR and pre-push workflows instead of duplicating them here.

## Comments and reporting

Keep comments explaining non-obvious intent or constraints. Update comments made obsolete by the change; avoid unrelated deletion campaigns. Use `no-comments` only for an explicitly requested comment audit, not as a prerequisite for every review.

Lead with the outcome, then the verification and unresolved decisions. Use concrete paths or artifact references when helpful. Keep reports proportional to the task. The `unslop` skill owns prose cleanup; this mode does not add another style checklist.

For a pause, handoff, or unattended run, follow [monitoring and continuation](../pstack-runtime/references/monitoring.md). Use a compact checkpoint rather than a mandatory decision log for every task. Detailed trails are for work that needs an audit record and remain local unless publication is authorized.

## Optional workflows

Use a specialized playbook only for an explicitly requested workflow or a task that needs its additional proof. Its prescribed steps cannot expand authority or assume unavailable tools; the execution contract governs those cases. These are not mandatory follow-up steps to the default workflow.

- Evidence gathering: [investigation](playbooks/investigation.md), [runtime forensics](playbooks/runtime-forensics.md), [trace forensics](playbooks/trace-forensics.md).
- Focused engineering: [bug fix](playbooks/bug-fix.md), [feature](playbooks/feature.md), [refactoring](playbooks/refactoring.md), [performance](playbooks/perf-issue.md).
- Design experiments: [prototype](playbooks/prototype.md), [visual parity](playbooks/visual-parity.md), [hillclimb](playbooks/hillclimb.md).
- Skills: [authoring](playbooks/authoring-a-skill.md), [evaluation](playbooks/eval.md).
- Delivery when authorized: [PR creation](playbooks/opening-a-pr.md), [PR follow-up](playbooks/babysit.md), [shipping](playbooks/shipping.md), [multi-PR planning](playbooks/multi-phase-plan.md).
- Explicit long-running work: [autonomous run](playbooks/autonomous-run.md), [orchestration](playbooks/orchestrate.md), [independent PR queue](playbooks/autopilot-full.md), [stacked PR queue](playbooks/autopilot-stack.md).
- Continuity: [session pickup](playbooks/session-pickup.md), [safe pause](playbooks/pause-safely.md), [worktree cleanup](playbooks/worktree-cleanup.md).
