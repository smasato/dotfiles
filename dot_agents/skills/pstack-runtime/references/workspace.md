# Local workspace conventions

These are deployment and tooling conventions for this dotfiles setup, not requirements of the execution contract on other machines.

## Skills

- Edit global skills in their chezmoi source. Locally maintained skills are not reinstalled from their upstream source.
- Shared global skills live in `~/.agents/skills`; shared project skills normally live in `.agents/skills`. Preserve existing project layout and invocation policies. Add host-specific links only when discovery requires them.
- Follow the installed `writing-for-agents` guidance when editing skills. Use an available skill-authoring helper when useful; its absence is not a blocker.
- Resolve paths relative to the containing skill. A playbook under `poteto-mode/playbooks/` that names `scripts/` means `poteto-mode/scripts/`, not the target repository. Give workers resolved paths.
- Keep private history outside public repositories. Reusable instructions contain general rules, not transcripts, session identifiers, employer or customer names, internal URLs, or task-specific evidence. Audit new documentation and examples before publishing.

## Worktrees and stacks

Use the installed `wt-worktree-ops` skill for worktree operations and `gh-stack` for stacked PRs. `gh stack view --json` supplies topology; GitHub supplies current PR heads and checks. Only the designated stack owner changes topology.

The optional orchestration CLI can load the current stack with `orch frontier set --repo <path>`. For an explicitly independent PR queue, use `--prs <bottom-to-top-numbers>`; the CLI validates PRs against GitHub.

The watcher and store use Bun with locked dependencies installed during dotfiles deployment. Runtime commands do not install packages implicitly. GitHub operations need authentication; stack operations also need the gh-stack extension and repository support. Report missing prerequisites rather than inventing substitutes.

## Long-running commands and external services

Use the `pueue` skill for shell commands expected to take minutes. Retain task IDs and inspect exit status and logs. A queued command does not grant permission or provide autonomous model turns.

The Bot UI skill is a client for an existing webhook service. It does not create a scheduler or supply host-specific continuation capabilities.
