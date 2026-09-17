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

## Update fx

fx is installed by mise from `github:vercel-labs/fx`. The initial install runs
when the managed mise configuration changes. To install a newer release later,
upgrade it explicitly from `$HOME` so a repository-local `mise.toml` cannot
affect resolution:

```bash
(cd "$HOME" && mise upgrade github:vercel-labs/fx)
```

## Experimental OMP profile

Run `omp --profile experimental` for personal Claude, Codex, OpenCode Go / Zen,
and SuperGrok experiments. Its config, credentials, sessions, and caches are separate from the
default OMP profile. Only the OMP instruction overlay and custom agent definitions
are shared through symlinks.

Authenticate inside this profile with `/login anthropic` for a Claude subscription
and `/login openai-codex` for a ChatGPT subscription. These use OAuth, not paid API
keys. For the other providers, use `/login opencode-go`, `/login opencode-zen`,
and `/login xai-oauth` with the personal OpenCode API key and SuperGrok account.
Credentials are not copied from the default profile or stored in this repository,
so logging in to the default profile does not authenticate this profile.

Initial assignments use Kimi K2.7 Code for the main model, GLM-5.3-Flash for
lightweight work, MiniMax M3 for task agents, Kimi K3 for planning, GLM-5.2 for
review, and Grok 4.6 via OAuth for deeper analysis and vision. Zen's Big Pickle is
a comparison model. The model switcher cycles through `default`, `slow`, `review`,
and `zen`. The advisor is off initially to avoid consuming quota on every turn.

Claude and Codex models are included in the model picker without changing the
existing model assignments. The profile disables the `openai`, `devin`, and paid
`xai` backends. This is configuration isolation, not a sandbox: project settings,
environment credentials, and explicit command-line overrides still apply. Use
OAuth login rather than `ANTHROPIC_API_KEY` to use the Claude subscription. Keep work repositories out of
personal experiments.

Model assignments are initial defaults; changes made inside OMP survive
`chezmoi apply`. Inspect them with
`omp --profile experimental config get modelRoles --json`.
[Go limits vary by model](https://opencode.ai/docs/go/). Enabling **Use balance**
in the OpenCode console permits Go overages to consume Zen credits. SuperGrok
OAuth model access depends on the subscription; catalog presence alone does not
prove account access.

# Configure hk

```bash
hk install
```
