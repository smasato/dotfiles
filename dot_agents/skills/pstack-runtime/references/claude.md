# Claude Code execution

- Spawn with the current `Agent` tool. Use `subagent_type: "pstack-worker"` for ordinary pstack children. This definition uses `model: inherit`; omitting a model really inherits, unlike this setup's Opus-pinned `general-purpose`.
- Resolve `fast` to `haiku`, `code` to `sonnet`, and `judgment` by omitting the model. The default `review-panel` is inherited model, `opus`, and `sonnet`. Deduplicate equivalent models. If only one model is available, use separate fresh reviewers and describe the result as independent passes, not model diversity. An explicitly requested model takes precedence when supported.
- For comment review, use `subagent_type: "comment-sicko"`. It reads the shared reviewer prompt under `no-comments/references/`.
- Use `run_in_background: true` only when the current Agent schema supports it and the parent can continue useful work. Collect the returned result or use the host's exposed task output / task management tools. Send new work through the host's supported resume/message operation, not a fabricated tool name.
- Do not pass a cloud environment or a read-only boolean to Agent. Use the available worktree isolation option when appropriate, or prepare a separate worktree through `wt-worktree-ops` and give the child an exact working directory. For read-only subtasks, set the scope in the brief and use a restricted agent when one fits.
- Use the available todo/plan tool for multi-step work. If none is exposed, keep a short checklist in the conversation or task artifact.
- Ask missing-information questions with the current question tool when available; otherwise ask in plain text. Honor already granted authority.
