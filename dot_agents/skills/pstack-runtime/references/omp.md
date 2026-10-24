# OMP adapter

Read this reference when a workflow needs OMP delegation, model selection, history, or continuation. The [execution contract](../SKILL.md) and [delegation rules](delegation.md) own scope, ownership, and verification.

## Skills and delegation

Shared skills resolve through `skill://<name>`. Tell the user to invoke `/skill:<name>`; hidden, explicitly invoked skills remain reachable through this command. Use the current tool schema rather than another host's argument names.

Dispatch independent work in one `task` batch with shared `context` and per-item `task` and `solutionSpace`. Omit `agent` for the default implementation worker. Use `scout` for read-only research, `sonic` for mechanical work, and a matching specialist when available. A brief must include the verified working directory, revision, writable scope, and expected evidence; a path in the brief does not create isolation.

Resolve model selections from the active `modelRoles`, `task.agentModelOverrides`, and agent definitions. A task-level override wins over agent frontmatter. Role names describe selections, not callable agents; ordinary task dispatch selects an agent rather than passing a model ID.

| pstack work    | OMP selection                                                                                                                            |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `fast`         | `scout` or `sonic`, normally routed through `@smol`                                                                                      |
| `code`         | Default `task` worker, normally routed through `@task`                                                                                   |
| `judgment`     | Planning uses `@plan`; review uses `@review` or the review panel below. OMP's lightweight `@judge` role is not the pstack judgment role. |
| `review-panel` | For read-only review, `pstack-review-openai` and `pstack-review-anthropic`, backed by `@review_openai` and `@review_anthropic`           |

## Independent review

For `interrogate`, resolve both panel agents before dispatch and report their concrete models. Give each the same intent, frozen diff or files, rubric, and code-quality lens. Label them Reviewer A and Reviewer B and submit them together. Keep their findings independent until both finish.

The panel agents expose source-reading tools, not shell, editing, or delegation tools. The parent supplies the diff and any runtime evidence. These agents are reviewers, not write-capable `arena` candidates; use available implementation agents for candidates and disclose any model-diversity limitation.

After execution, check the actual models in OMP's agent metadata or transcripts, including any fallback. Different agent names, providers, or reasoning levels alone do not establish different model families. If settings collapse the panel to one family, or a reviewer cannot run, report the reduced coverage instead of claiming a multi-family review. Use another available reviewer only within the user's constraints; configuration changes are a separate action.

Model choices live in OMP configuration, not a second pstack model-rules file. The ordinary `reviewer` and its `@review` setting remain independent of this panel. Consult `omp://task-agent-discovery.md` when model precedence or discovery behavior is unclear.

## History

Use the eval `archive` API to select sessions by workspace, time, and topic before reading transcripts. Read `xd://eval/archive` for its current interface. Summaries locate evidence; the recorded calls and results prove execution. Use `seance` with a specific `sourceSession` for a read-only historical consult, not to resume that session's work. Follow the [scoped history rules](history.md).

## Completion and continuation

Task results arrive automatically. Continue independent work while workers run; use `wait` only when blocked. Address active workers through `agent://<id>` and owned processes through `proc://<id>`. An agent's completion report is not verification of its artifacts.

For a long-running CLI watcher, use the exposed background-process mechanism and retain its handle. A watcher does not supply model turns after OMP exits. Follow the [handoff procedure](monitoring.md) before stopping; on resume, reconcile the actual workers, processes, revision, and remaining authorization. A persisted session is a recovery record, not a promise of unattended execution.
