# dotfiles

Masato Sugiyama's macOS dotfiles, managed with [chezmoi](https://github.com/twpayne/chezmoi).

## Setup

With chezmoi installed, initialize the configuration, review the changes, and apply:

```sh
chezmoi init smasato
chezmoi diff
chezmoi apply
```

Initialization asks for your email, 1Password account, work/personal profile, and machine role.

## Common commands

| Command                                              | Purpose                       |
| ---------------------------------------------------- | ----------------------------- |
| `chezmoi diff`                                       | Preview pending changes       |
| `chezmoi apply`                                      | Apply local changes           |
| `chezmoi update`                                     | Pull and apply remote changes |
| `chezmoi add <path>`                                 | Track a file from your home   |
| `mise self-update`                                   | Update mise itself            |
| `(cd "$HOME" && mise upgrade github:vercel-labs/fx)` | Update fx using global config |

## chezmoi diff

[`.chezmoi.toml.tmpl`](.chezmoi.toml.tmpl) excludes always-run scripts from
`chezmoi diff`. File changes and pending `run_once` / `run_onchange` scripts remain
visible. `chezmoi apply` still runs always-run scripts, even when the diff is empty.
Use `chezmoi diff --exclude=none` to inspect them.

After changing `.chezmoi.toml.tmpl`, run `chezmoi init` in the configured source
directory to regenerate the local configuration. `chezmoi apply` alone does not
regenerate it.

In a worktree, add `--source "$(git rev-parse --show-toplevel)"` to chezmoi
commands to use that checkout.

## Configuration

| Area              | Source                                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------------------------- |
| Homebrew packages | [`.chezmoidata/packages.yaml`](.chezmoidata/packages.yaml)                                                 |
| CLI tools         | [`dot_config/mise/config.toml.tmpl`](dot_config/mise/config.toml.tmpl)                                     |
| Shell             | [`dot_zshrc.tmpl`](dot_zshrc.tmpl), [`dot_zprofile.tmpl`](dot_zprofile.tmpl)                               |
| Applications      | [`dot_config/`](dot_config/)                                                                               |
| Setup scripts     | [`.chezmoiscripts/`](.chezmoiscripts/)                                                                     |
| AI agents         | [`dot_claude/`](dot_claude/), [`dot_codex/`](dot_codex/), [`dot_grok/`](dot_grok/), [`dot_omp/`](dot_omp/) |

Setup installs mise at `~/.local/bin/mise` using the standalone installer, not Homebrew.

OMP also has [experimental](dot_omp/private_profiles/experimental/) and
[security](dot_omp/private_profiles/security/) profiles. Start them with
`omp --profile experimental` or `omp --profile security`. Each profile keeps its
own credentials and sessions. This is not a sandbox: project settings, environment
credentials, and CLI overrides still apply. Use OAuth login for subscription
access and keep work repositories out of personal experiments.

## Guides

- [Herdr](docs/herdr.md)
- [Worktrunk](docs/wt.md)
- [Claude accounts](docs/claude-accounts.md)
- [Plannotator](docs/plannotator.md)
- [pstack](docs/pstack/README.md)

## Development

Install Git hooks once, then run the repository checks before committing:

```sh
hk install
hk check
```
