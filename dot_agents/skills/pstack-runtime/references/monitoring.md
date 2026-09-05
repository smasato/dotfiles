# Monitoring and continuation

Define a stop predicate and the user's authorized actions before starting. A request to monitor is not permission to merge, post comments, or deploy.

- Claude Code: use the host's available recurring task or Monitor capability. If a user-facing `/loop` command is supported, use it through the documented interface rather than running it as a shell command. Otherwise launch the watcher through the supported background task mechanism and collect its output during the active session.
- Codex: use the exposed wait tools and watcher output. Create a persisted goal only when the user explicitly requested a goal and the host exposes goal tools. A playbook cannot supply that authorization. Without a goal feature, track the objective in the task artifact and continue within the session.
- For either host, if no scheduler is exposed, poll with bounded waits and report progress. For a 30-minute audit cadence, record the next deadline and use short interruptible waits between useful work; do not block the conversation for 30 minutes.
- A watcher process reports state; it cannot wake a stopped model unless the host supplies that capability. Do not promise execution after closing the session or restarting the client. Persist a checkpoint with objective, owner/agent handles, branches, task IDs, verification evidence, and the next command. After restart, inspect actual process/task state before resuming or replacing workers.
- Use the `pueue` skill for shell commands expected to run for minutes in this dotfiles environment. Retain the task ID, collect its exit status and logs, and clean up only tasks owned by this run. A queued process does not bypass execution permission or substitute for model continuation.
- On explicit stop, interrupt owned workers and watchers, then record the checkpoint. Unchanged CI state is an expected wait state.
