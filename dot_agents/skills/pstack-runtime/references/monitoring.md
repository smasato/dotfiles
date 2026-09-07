# Monitoring and continuation

Define a stop condition and authorized actions before starting. Monitoring is not permission to merge, post comments, or deploy.

## Wait within the available capabilities

Use the host's exposed wait, notification, background-task, or scheduling tools. If no scheduler is available, use bounded, interruptible waits during the active session. Report progress when the state changes or a decision is needed; unchanged CI is an expected wait state.

A watcher process reports state. It cannot wake a stopped model unless the host supports that capability. Do not promise execution after session closure or restart. Create a persistent goal only when explicitly requested and supported. Use the [local queue convention](workspace.md) for long-running shell commands.

## Stop at the requested boundary

- On an immediate stop request, stop dispatching new work and interrupt owned workers and watchers where possible. Report any process that could not be stopped.
- On "finish the active workers, then pause", drain those workers but start no new tasks. Do not turn pause into commit, push, merge, or cleanup unless those actions were authorized.
- Preserve local changes and record any incomplete operation. A checkpoint does not require a WIP commit or a stash. Do not discard work to make the tree look clean.

## Leave a compact handoff

Use an existing task artifact when available; otherwise write a local note outside version control. Include only what another session needs:

- Objective, authorized actions, and stop condition.
- Repository, worktree, branch, base and head revisions, and uncommitted changes.
- Completed work, remaining tasks, and decisions waiting on the user.
- Checks run, their target revision or local state, results, and unverified areas.
- Worker, process, and queue handles with their owners and last observed state.
- The next permitted action.

On resume, verify the actual repository, task, and process state before continuing or replacing workers. Reconcile the note with current artifacts to avoid repeating completed work. Follow the [privacy boundary](workspace.md) for notes and history.
