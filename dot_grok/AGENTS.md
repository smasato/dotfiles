# Grok overlay

- Address me as Masato.
- Plans and error explanations in Japanese. Keep command output and log lines in the original language.
- Claude agent frontmatter models (`haiku` / `sonnet` / `opus` / `fable`) are invalid here.
  - search / lint / mechanical edit → `code-locator` / `chore-worker` / `check-runner` / builtin `explore` (prefer `grok-4.5`)
  - normal multi-step work → `general-purpose-sonnet` or parent `grok-4.6`
  - design / hard debug / deep review → parent session or `deep-reviewer` on `grok-4.6`
- Worktrees: use the `wt-worktree-ops` skill (`wt`). Do not use Grok `/new` worktrees.
- Long commands (≥ ~2 min): enqueue with the `pueue` skill.
- `ugrep` is installed: use it for compressed files / archives (`-z`), fuzzy matching (`-Z`), boolean queries (`-%`), hexdump / binary search (`-X`).
- `ast-grep` (`sg`) is installed: structural code search and same-shape rewrites across files (`--pattern ... --rewrite ...`) instead of grep / sed.
- `ghq` is installed: clone with `ghq get <url>` (lands under `~/dev/src/<host>/<owner>/<repo>`).
- `shellcheck` is installed: run it on any shell script you create or edit.
- macOS `sed` / `awk` / `date` are BSD. GNU versions: `gdate`, `gawk`. No `gsed`; in-place edits use `sed -i ''` or `perl -pi -e`.
- `yq` is installed: read / edit YAML / TOML / JSON structurally instead of sed.
- Never `git commit --no-verify`. Conventional commits.
