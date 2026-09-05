# Scoped history

Prefer the active conversation, an exact transcript path supplied by the host, or its native history search. For a retrospective, establish the workspace, time range, topic, and excluded current session first.

- Claude Code stores sessions below `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/`. Use only the project directory matching the requested workspace, confirm `cwd` in the records, and include subagent records only when auditing that session. pclaude has a separate projects directory; do not silently combine accounts.
- Codex clients may keep JSONL sessions under `${CODEX_HOME:-$HOME/.codex}/sessions/` and `archived_sessions/`. Filter session metadata by the exact workspace before reading conversation bodies. Prefer host history search when local logs are not available. Do not recursively search other projects' message bodies to discover a session.
- Claude JSONL tool events generally appear as message content blocks with `type: "tool_use"`, plus tool results. Codex rollout records use typed envelopes such as `session_meta`, `response_item`, and `event_msg`; function calls can appear as response items. Inspect the actual format before parsing. Both shell-based file reads and dedicated Read calls can be evidence of a skill read.
- For an active transcript, verify session identity with metadata and the opening task. Do not assume the first line is a user message or that each line is a chat message.
- If history is unavailable, give workers a digest of observed work. Mark transcript-dependent evaluation INCONCLUSIVE; a digest is not evidence of tool execution. For resuming work, use repository state, PRs, task ledgers, and the digest to proceed.

The worktree audit accepts an explicit scoped transcript directory as its second argument. Missing history is unknown, never proof that a worktree is abandoned.
