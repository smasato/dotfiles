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

Lazygit 0.65.1 uses [`git.diffRenderers[].command`](https://github.com/jesseduffield/lazygit/blob/v0.65.1/docs/Custom_DiffRenderers.md)
for Delta. Keep the managed configuration in that format rather than restoring
the older `git.pagers[].pager` keys when resolving drift.

References: [diff configuration](https://www.chezmoi.io/reference/configuration-file/variables/#diffexclude),
[entry types](https://www.chezmoi.io/reference/command-line-flags/common/#available-entry-types),
[configuration template](https://www.chezmoi.io/reference/special-files/chezmoi-format-tmpl/).

## Agent hooks

Moshi's agent hooks are disabled. The `moshi-hook` package remains installed for
the Moshi client and SSH/Mosh integration. To remove existing global hook
registrations and extensions while preserving unrelated hooks, run:

```bash
moshi-hook uninstall
```

Claude's work account and all three Codex work accounts share their personal
account's hook configuration, so this also disables Moshi for those accounts.
Restart running agent sessions to unload extensions already in memory.
`chezmoi apply` does not restore Moshi hooks. Running `moshi-hook install`
explicitly enables them again.

Claude's settings template preserves Superset's notification hooks and its
`Artifact` guard. They run only when `SUPERSET_HOME_DIR` points to executable
hook scripts. Orca uses the simplified macOS hook command, including for
`SessionEnd`.

## mise

mise is not installed from Homebrew. When `~/.local/bin/mise` is missing,
`run_onchange_after_01-mise-install` installs it with the official standalone
installer, rebuilds the shims, and then installs the managed tools. Scripts and
configs that call mise use this path. Update mise itself with `mise self-update`.

Applying on a machine that has the old Homebrew formula also installs the
standalone binary. `chezmoi apply` does not remove the formula. Remove it
with:

```bash
brew uninstall mise
```

## Update fx

fx is installed by mise from `github:vercel-labs/fx`. The initial install runs
when the managed mise configuration changes. To install a newer release later,
upgrade it explicitly from `$HOME` so a repository-local `mise.toml` cannot
affect resolution:

```bash
(cd "$HOME" && mise upgrade github:vercel-labs/fx)
```

## OMP settings

The default and security OMP profiles enforce `advisor.reviewInterval: 3` on `chezmoi apply`.
The advisor reviews every third eligible primary update, with skipped updates
included in the next review.

The default profile uses a custom status line, a full subagent list, and
`task.maxConcurrency: 8`. Its `Ctrl+P` cycle is `smol`, `default`, `slow`.
The security profile inherits unset display and concurrency settings while
preserving existing overrides and its model cycle.

The default, experimental, and security profiles enforce
`telemetry.otlpExportEnabled: false` on `chezmoi apply`, disabling OTLP trace,
log, and metric export even when `OTEL_*` endpoints are configured.

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

## Security OMP profile

Run `omp --profile security` for Devin-based implementation with Daybreak-capable
Codex review. On first apply, the profile starts from the default profile's current
settings and managed defaults, then applies these model assignments:

| Role              | Initial model                    |
| ----------------- | -------------------------------- |
| `default`, `task` | `devin/glm-5-3-1m:high`          |
| `slow`, `plan`    | `devin/glm-5-3-1m:max`           |
| `smol`, `vision`  | `openai-codex/gpt-6-luna:medium` |
| `judge`           | `openai-codex/gpt-6-luna`        |
| `tiny`            | `openai-codex/gpt-6-luna:low`    |
| `review`          | `openai-codex/gpt-6-sol:high`    |
| `advisor`         | `openai-codex/gpt-6-luna:high`   |

The advisor remains enabled and reviews every third eligible primary update.
`devin/deepseek-v4-pro` and `openai-codex/gpt-6-luna` remain available for manual
selection. Judge fallback uses `openai-codex/gpt-6-sol`. Unlike chat roles,
`judge` does not use a thinking suffix; `chezmoi apply` removes these suffixes
from existing judge selectors and their fallback entries without changing models.

The profile has its own config, sessions, model cache, and credential store
(`agent.db`). It shares only the default profile's `AGENTS.md` and custom agent
definitions through symlinks. OMP rotates across every stored account of a
provider, so keep accounts meant only for security reviews, such as a personal
Daybreak account, in this store. Accounts logged in here are not used by the
default profile, and login, logout, and credential refresh affect only this
profile. Log in to each provider the roles use:

```sh
omp --profile security login devin
omp --profile security login openai-codex
```

Account preferences belong in the profile's local `auth.accountPolicies`, using
an `accountId` obtained from the authenticated account. The repository does not
specify an email address or account ID. Existing local policies survive
`chezmoi apply`. Select an account with confirmed Daybreak access; a Pro plan alone
does not establish eligibility.

OMP requests Daybreak Blue when the selected account's model catalog advertises
it for Sol or Luna. Account priority is not exclusive routing: another account
may serve requests after rotation. Daybreak approval does not apply to Devin
models. Project settings and explicit CLI overrides still take precedence.

Changes made inside the security profile survive `chezmoi apply`; its settings do
not continuously mirror changes to the default profile. Inspect or select a role:

```sh
omp --profile security config get modelRoles --json
omp --profile security --model @review
omp --profile security --model devin/deepseek-v4-pro
```

# Configure hk

```bash
hk install
```
