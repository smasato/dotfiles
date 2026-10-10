# OMP overlay

- Address me as Masato.
- Respond and present plans in Japanese. Keep command output and logs unchanged.
- At the start of each session, read `~/.agents/skills/caveman/SKILL.md` and use caveman mode at `full` intensity by default. Honor explicit mode changes, including `stop caveman` and `normal mode`. Keep persisted writing in normal prose.
- Use the `wt-worktree-ops` skill for worktrees. Do not use OMP `/wt`.
- Use the `pueue` skill for finite commands expected to run for about two minutes or more.
- Run interactive services, watchers, and REPLs as bash services (`name` + `ready`); manage them via `proc://`.
- Clone repositories with `ghq get`.
- Run `shellcheck` on shell scripts you create or edit.
- Use `ugrep` only when OMP's `grep` cannot handle the input, such as compressed files, archives, fuzzy matching, or binary searches.
- macOS provides BSD `sed`, `awk`, and `date`; use `gdate` or `gawk` when GNU behavior is required.
- Do not bypass commit hooks with `--no-verify`. Use Conventional Commits.
- Do not edit `README.md`, `docs/`, or changelogs unless I ask. This overrides the default rule to update docs/changelog after fixes and features.
