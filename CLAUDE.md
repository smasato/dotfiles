# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a chezmoi-managed dotfiles repository for a macOS development environment. The repository contains configuration files, scripts, and templates that are deployed to the home directory using chezmoi.

## Commands

### Dotfiles Management
- **Apply changes**: `chezmoi apply` - Apply configuration changes to the home directory
- **Add file**: `chezmoi add <file>` - Add a file to chezmoi management
- **Edit file**: `chezmoi edit <file>` - Edit a managed file
- **Diff changes**: `chezmoi diff` - See what changes will be applied
- **Update from repo**: `chezmoi update` - Pull and apply latest changes

### Homebrew Management
- **Update bundle files**: `ruby scripts/brew.rb` - Regenerates brew YAML files from current system
- **Install from bundle**: `brew bundle --file=brew_base.yml` - Install packages from bundle file

### Shell
- **Reload shell**: `reload` (alias for `exec zsh`)

## Architecture

### Directory Structure
- `/dot_*` files: Templates that get deployed to home directory (the `dot_` prefix becomes `.`)
- `/private_*` files: Templates with sensitive data (uses 1Password integration)
- `/scripts/`: Utility scripts for system management
- `/brew_*.yml`: Homebrew bundle files (base, personal, work profiles)

### Key Technologies
- **Dotfiles Manager**: chezmoi with templating support
- **Shell**: Zsh with Powerlevel10k, Antigen for plugin management
- **Runtime Management**: mise (formerly rtx) for managing language versions
- **Package Management**: Homebrew for system packages
- **IDE**: Cursor (VS Code fork) with curated extensions
- **Secrets**: 1Password CLI integration for sensitive values

### Template Variables
Templates use Go templating with chezmoi. Common variables:
- `{{ .email }}`: User email (set during chezmoi init)
- `{{ .chezmoi.homeDir }}`: Home directory path
- `{{ .chezmoi.sourceDir }}`: Chezmoi source directory
- Conditional logic based on installed tools: `{{ if lookPath "brew" }}`

### Configuration Patterns
- Environment-specific configs using chezmoi templates
- Work vs personal profile differentiation
- 1Password integration for secrets (private_* files)
- Lazy loading and conditional sourcing based on tool availability