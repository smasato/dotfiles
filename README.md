# github.com/smasato/dotfiles

Masato Sugiyama's dotfiles, managed with [`chezmoi`](https://github.com/twpayne/chezmoi).

Install them with:

    chezmoi init smasato

## chezmoi diff

`.chezmoi.toml.tmpl` sets `[diff] exclude = ["always"]` to hide scripts that run
on every apply, including antigen, bat, and Claude Worktrunk updates. Regular file
diffs and pending `run_once` / `run_onchange` scripts remain visible.
`chezmoi apply` still executes the scripts normally.

After updating this template in the configured source directory, run `chezmoi init`
to regenerate the local configuration. `chezmoi apply` alone does not regenerate it.
In a worktree, pass `--source "$(git rev-parse --show-toplevel)"` to chezmoi commands
to use that checkout.

Use `chezmoi diff --exclude=none` to inspect all pending scripts, including edits
to always-run scripts. A regular `chezmoi diff` can be empty while those scripts
are still scheduled to run.

References: [diff configuration](https://www.chezmoi.io/reference/configuration-file/variables/#diffexclude),
[entry types](https://www.chezmoi.io/reference/command-line-flags/common/#available-entry-types),
[configuration template](https://www.chezmoi.io/reference/special-files/chezmoi-format-tmpl/).

# Configure hk

```bash
hk install
```
