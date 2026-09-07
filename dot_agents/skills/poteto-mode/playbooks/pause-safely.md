### Pause safely

Follow [monitoring and continuation](../../pstack-runtime/references/monitoring.md), which owns stop semantics and the handoff fields.

1. Confirm the requested boundary: interrupt now, or finish active workers and then pause. Stop dispatching new work and inform every affected worker.
2. Preserve the current working state. Do not create a WIP commit, stash changes, push, or clean up unrelated work merely to pause. Use those operations only when already authorized and safe for other writers.
3. Collect available results and record the compact handoff in an existing task artifact or a local note outside version control. Name incomplete operations and anything that could not be stopped.
4. Report where the checkpoint lives and the next permitted action. On resume, verify actual repository and process state before following the note.

A request to keep working unattended is not a pause request. It still needs a stop condition and does not provide a scheduler or permission beyond the agreed task.

**Reply:** completed and pending work, verification status, any active workers, checkpoint location, and the first action on resume. State whether local changes remain uncommitted.
