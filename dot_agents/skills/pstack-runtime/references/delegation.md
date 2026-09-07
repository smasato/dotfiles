# Delegation

Parallelize independent investigation, implementation, and verification when it helps the task. Keep tightly coupled work with one owner. Do small local tasks directly when delegation would add more coordination than useful work.

## Assign ownership before starting

Each brief includes the goal, working directory, base revision, writable files or worktree, forbidden actions, acceptance checks, and report format. The parent owns the enclosing workflow; children receive bounded subtasks rather than recursively launching the same workflow.

- Give independent writers separate worktrees where practical. In a shared worktree, assign disjoint files and one owner for repository-wide operations.
- The repository owner coordinates commits, branch switches, rebases, stash, resets, lockfile updates, and broad formatters. A child must not use whole-tree operations to make its own check pass.
- Include hook side effects in this ownership boundary. A commit hook that stashes changes or formats files requires other writers in that worktree to pause.
- Shared browser sessions, test data, ports, and dev servers need owners too. Isolate them or serialize their use; separate source files alone do not isolate runtime state.
- Verify the actual working directory and revision. A path in a prompt is not enforced isolation. Read-only instructions are not a sandbox.

## Select available models

`fast`, `code`, `judgment`, and `review-panel` describe work, not model IDs. Use an available lower-cost model for mechanical work, a capable coding model for implementation, and stronger reasoning for ambiguous diagnosis or design. Resolve actual models from the host's current configuration. Do not assume fixed model families or unlimited concurrency.

Use distinct models or fresh reviewers when independent judgment is part of the task. If delegation is unavailable, perform sequential passes and label them self-review. If independent review or a model race is required, report the limitation rather than claiming an equivalent result.

## Collect and verify

Continue useful parent work while children run. Collect terminal results and inspect the actual diffs, artifacts, and checks. Separate each result into completed, blocked, or requiring a decision. A child saying "done" does not prove acceptance.

For a moving branch or stack, keep one topology owner. Give workers the current base and head. When either changes, notify affected workers, pause stale write operations, and reassess their findings against the new revision before publishing or merging.

On a scope change or stop request, send the new boundary to every affected worker. Start no new tasks beyond it. Use the [handoff procedure](monitoring.md) when work must continue in another session.
