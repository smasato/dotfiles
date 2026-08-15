# Grok overlay

- Address me as Masato.
- Plans and error explanations in Japanese. Keep command output and log lines in the original language.
- Claude agent frontmatter models (`haiku` / `sonnet` / `opus` / `fable`) are invalid here.
  - search / lint / mechanical edit → `code-locator` / `chore-worker` / `check-runner` / builtin `explore` (prefer `grok-4.5`)
  - normal multi-step work → `general-purpose-sonnet` or parent `grok-4.6`
  - design / hard debug / deep review → parent session or `deep-reviewer` on `grok-4.6`
- Worktrees: use the `wt-worktree-ops` skill (`wt`). Do not use Grok `/new` worktrees.
- Long commands (≥ ~2 min): enqueue with the `pueue` skill.
- Never `git commit --no-verify`. Conventional commits.
