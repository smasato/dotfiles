# Codex overlay

- `ugrep` is installed: use it for compressed files / archives (`-z`), fuzzy matching (`-Z`), boolean queries (`-%`), hexdump / binary search (`-X`).
- `ast-grep` (`sg`) is installed: structural code search and same-shape rewrites across files (`--pattern ... --rewrite ...`) instead of grep / sed.
- `ghq` is installed: clone with `ghq get <url>` (lands under `~/dev/src/<host>/<owner>/<repo>`).
- `shellcheck` is installed: run it on any shell script you create or edit.
- macOS `sed` / `awk` / `date` are BSD. GNU versions: `gdate`, `gawk`. No `gsed`; in-place edits use `sed -i ''` or `perl -pi -e`.
- `yq` is installed: read / edit YAML / TOML / JSON structurally instead of sed.

## UI/UX verification

For UI/UX specification discussions, visual reviews, and verification of UI changes, load `~/.agents/skills/ui-ux-verification/SKILL.md` before making claims about appearance or interaction. Use the `agent-browser` skill for browser operation. If the required skill, browser, or image input is unavailable, state the limitation and distinguish verified behavior from assumptions.
