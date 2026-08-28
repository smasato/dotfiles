# pstack Model Configuration

pstack per-role model choices (the `/setup-pstack` rule). These override the
inline defaults in the pstack skills (`poteto-mode`, `how`, `why`, `arena`,
`swarm`, `architect`, `interrogate`, `reflect`), whose default slugs are
Cursor model names that do not exist here. Valid Agent-tool models in Claude
Code are `sonnet` / `opus` / `haiku` / `fable`; `inherit-parent` means omit
the Task `model` so the role runs on the parent session model.

- feature, refactoring: sonnet
- bug-fix, perf-issue, hillclimb: opus
- judgment and prose: inherit-parent
- hardest tasks: inherit-parent
- how explorer: sonnet
- how explainer: inherit-parent
- how critics: fable, opus, sonnet
- why investigators: sonnet
- why synthesizer: inherit-parent
- reflect tooling: sonnet
- reflect judgment, divergent, synthesizer: inherit-parent
- arena runners: fable, opus, sonnet
- arena cross-judge pool: fable, opus, sonnet
- swarm workers: sonnet
- architect runners: fable, opus, sonnet
- interrogate reviewers: fable, opus, sonnet
