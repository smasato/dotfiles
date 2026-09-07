# Claude Code adapter

Use this reference only for Claude Code tool mappings or history format. The [execution contract](../SKILL.md) and [delegation rules](delegation.md) own workflow behavior.

## Delegation

- Inspect the current `Agent` schema and installed agent definitions. Use `pstack-worker` when available for inherited-model work; select an available specialized agent or explicit model for cheaper bounded tasks. Resolve models from current configuration rather than treating role names as model IDs.
- For comment review, `comment-sicko` is an optional wrapper around `no-comments/references/comment-sicko.md`. If that definition is unavailable, pass the shared prompt to an available worker.
- Use background execution, task collection, messaging, and worktree isolation only when the current tools support them. Otherwise prepare an isolated workspace through the installed worktree workflow and pass its verified directory.
- Use plan and question tools when available and useful. A short checklist or a plain-text question is sufficient when they are absent.

## History

Claude Code stores sessions under `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/`. Select the directory for the requested workspace and confirm `cwd` and session identity before reading message bodies. Separate config directories are separate accounts; do not combine them without permission.

Tool calls commonly appear as `tool_use` content blocks and `tool_result` replies. Distinguish real user requests from `isMeta` content, task notifications, compaction summaries, and generated worker briefs. Inspect the actual record format before parsing. Include nested subagent logs only when auditing their parent session.
