# AGENTS.md

This file provides guidance to coding agents working with this repository.

## Repository Overview

This is a chezmoi-managed dotfiles repository for a macOS development environment. The repository contains configuration files, scripts, and templates that are deployed to the home directory using chezmoi.

## Commands

### Dotfiles Management

- **Apply changes**: `chezmoi apply` - Apply configuration changes to the home directory
- **Add file**: `chezmoi add <file>` - Add a file to chezmoi management
- **Edit file**: `chezmoi edit <file>` - Edit a managed file
- **Diff changes**: `chezmoi diff` - See what changes will be applied
- **Update from repo**: `chezmoi update` - Pull and apply latest changes
- `chezmoi diff` always shows `.chezmoiscripts/02-antigen.sh` and `03-bat.sh` as pending script runs. This is expected - ignore them when checking for unintended diffs

### Repo Tooling

- **Lint**: `hk check` - Run linters (prettier, pkl) defined in `hk.pkl`
- **Fix**: `hk fix` - Run linters with auto-fix
- Git hooks (pre-commit, pre-push) are managed by hk and run the same linters
- Repo-local tools (hk, prettier, pkl) are pinned in `mise.toml` at the repo root
- **Sort package YAML**: `mise run sort` - Sorts the package entries per profile (base/personal/work) under taps/brews/casks (yq task defined in `mise.toml`). Do not put comments in packages.yaml

### Shell

- **Reload shell**: `reload` (alias for `exec zsh`)

## Architecture

### Directory Structure

- `/dot_*` files: Templates that get deployed to home directory (the `dot_` prefix becomes `.`)
- `/private_*` files: Files deployed with restricted permissions (e.g. `private_Library/` for macOS `~/Library` files)
- `/dot_config/`: Deployed to `~/.config` - bat, ghostty, herdr, hunk, mise, nvim, atuin, karabiner, raycast, starship.toml
- `/dot_claude/`: Claude Code configuration - global CLAUDE.md, settings template, and a `skills` symlink to `~/.agents/skills`
- `/dot_claude_personal_home/`: Symlinks into `~/.claude` (settings, CLAUDE.md, agents, hooks, skills) so the `pclaude` alias (`CLAUDE_CONFIG_DIR=~/.claude_personal_home`, personal account) shares config while keeping its own `.claude.json` / sessions
- `/dot_grok/`: Grok Build configuration — global AGENTS.md overlay and `config.toml` (modify-template; Grok writes marketplace state)
- `/dot_agents/`: Deployed to `~/.agents` - canonical agent skills store (e.g. create-pr), shared across agents
- `/.chezmoidata/`: Data files for templates - `packages.yaml` (Homebrew packages)
- `/.chezmoiscripts/`: Install/setup scripts run by chezmoi (Homebrew packages, macOS defaults, agent skills, etc.)
- `/.chezmoiexternal.toml`: Externally fetched files (antigen.zsh, catppuccin themes, gitalias, tmux tpm)
- `/.github/PULL_REQUEST_TEMPLATE.md`: Pull request template

### Key Technologies

- **Dotfiles Manager**: chezmoi with templating support
- **Shell**: Zsh with Antigen for plugins and Starship for the prompt
- **Runtime/Tool Management**: mise for language runtimes (Ruby, Node, Bun, Python) and CLI tools, declared in `dot_config/mise/config.toml`
- **Package Management**: Homebrew - packages declared in `.chezmoidata/packages.yaml` and installed by a `.chezmoiscripts` run script during `chezmoi apply`
- **Git Hooks**: hk, configured in `hk.pkl`
- **Editors**: Cursor and Neovim (`dot_config/nvim`)
- **Terminal**: Ghostty, tmux, and Herdr; Atuin for shell history
- **Secrets**: 1Password CLI integration for sensitive values (e.g. `onepasswordDetailsFields` in templates)

### Template Variables

Templates use Go templating with chezmoi. Variables are prompted during `chezmoi init` (see `.chezmoi.toml.tmpl`):

- `{{ .email }}`: User email
- `{{ .work }}`: Work vs personal profile (selects Homebrew package sets, work-only config)
- `{{ .chezmoi.homeDir }}`, `{{ .chezmoi.sourceDir }}`: chezmoi built-ins
- Conditional logic based on installed tools: `{{ if lookPath "brew" }}`

### Configuration Patterns

- Environment-specific configs using chezmoi templates
- Work vs personal profile differentiation via the `work` variable
- 1Password integration for secrets in templates
- Conditional sourcing based on tool availability (`lookPath`)
- `run_onchange_*` scripts re-run when their embedded data hashes change (e.g. package list)
