# Codex adapter

Use this reference only for Codex tool mappings or history format. The [execution contract](../SKILL.md) and [delegation rules](delegation.md) own workflow behavior.

## Delegation

- Discover the collaboration tools actually exposed in this session. Clients differ in spawn, message, wait, and resume APIs. Use only their current names and arguments; do not infer a Claude `subagent_type` or an isolation guarantee.
- Pass the task, scope, verified working directory, input artifacts, and completion criteria. Keep the returned agent handle for follow-up and collection.
- Resolve role names to available models only when overrides are supported. Otherwise inherit and disclose limitations when model diversity was requested. Respect fork/history restrictions documented by the current host.
- For comment review, pass `no-comments/references/comment-sicko.md` or its full prompt to a fresh worker. For other workflows, give the relevant skill path and bounded subtask rather than delegating the enclosing workflow again.
- Use plan and question tools when available and useful; otherwise use a checklist or plain text. Preserve explicit-invocation policies in `agents/openai.yaml` when editing skills.

## History

Local clients may store JSONL under `${CODEX_HOME:-$HOME/.codex}/sessions/` and `archived_sessions/`. Prefer native scoped history search when local logs are unavailable. Filter by exact workspace metadata before reading message bodies.

Rollouts may use `session_meta`, `response_item`, and `event_msg` envelopes. User messages and function or custom-tool calls can appear as response items. Inspect the actual format rather than assuming every event is a message. Exclude injected context, child-generated instructions, and duplicated fork history from preference counts; tool results are required to prove execution.
