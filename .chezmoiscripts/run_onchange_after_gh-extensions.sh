#!/bin/bash

set -eu

# Install GitHub CLI extensions. Reruns when this list changes
# (e.g. when an extension is added below).
# gh extensions: github/gh-stack
#
# `gh extension install` needs an authenticated gh; on a fresh machine run
# `gh auth login` first, then `chezmoi apply` again.

# Rebuild PATH from scratch: mise env prepends its tool bin dirs, and dropping
# the inherited PATH keeps stale entries from shadowing them.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "${HOME}"
eval "$(mise env -s bash)"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh not found on PATH; run 'mise install' first" >&2
  exit 1
fi

extensions=(
  github/gh-stack
)

installed="$(gh extension list 2>/dev/null || true)"
for extension in "${extensions[@]}"; do
  if printf '%s\n' "${installed}" | grep -q "${extension}"; then
    echo "gh extension already installed: ${extension}"
  else
    echo "Installing gh extension: ${extension}"
    gh extension install "${extension}"
  fi
done
