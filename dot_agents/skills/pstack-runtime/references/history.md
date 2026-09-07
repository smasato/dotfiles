# Scoped history

Establish the workspace, time range, topic, and excluded sessions before reading history. Prefer the active conversation, an exact transcript path supplied by the host, or a native history search. Use a host adapter only when locating local logs or interpreting its event format.

1. Select candidates using workspace and session metadata before reading message bodies. Include related worktrees only after confirming their repository. Keep separate accounts separate unless explicitly included.
2. Check the actual task as well as the working directory. A session launched in a repository may concern unrelated work. Exclude local command-only sessions, generated worker prompts, and injected instructions from preference analysis.
3. Deduplicate retries, copied history, and parent/child reports. Count independent tasks, not repeated copies, before treating a pattern as a preference.
4. Read the relevant user messages and surrounding responses. Claims about tool execution require the actual calls and results, not just the assistant's summary. Inspect child logs only for the session being audited.
5. Distinguish repeated preferences, one-task decisions, agent suggestions, and observed failures. State sample bias and uncertainty. Do not infer a permanent rule from one correction.

If history is unavailable, use a digest of observed work for continuity and mark transcript-dependent claims unverified. Repository state and task artifacts can support a handoff, but a digest is not proof of unobserved execution.

When turning findings into shared instructions, keep evidence local and publish only general rules. Follow the [workspace privacy boundary](workspace.md). Remove temporary transcript extracts after analysis unless the user asks to retain them.

The worktree audit accepts an explicit scoped transcript directory as its second argument. Missing history is unknown, never proof that a worktree is abandoned.
