#!/bin/bash

set -eu

# Install global agent skills via the mise-managed `skills` CLI.
# Reruns when this list changes (e.g. when a skill is added below).
# skills: JuliusBrussee/caveman:*
# skills: github/gh-stack:gh-stack
# skills: shadcn/improve:improve
# herdr skills are written by run_onchange_after_herdr-plugins.sh from the
# installed herdr binary and plugin checkouts, not from this list.
#
# Target only the universal store: skills land in the canonical
# ~/.agents/skills, and ~/.claude/skills is a chezmoi-managed symlink to that
# directory. Adding claude-code as a target here would write a per-skill
# symlink through that directory symlink, creating a self-referencing link
# inside ~/.agents/skills. -y runs it non-interactively.

# Rebuild PATH from scratch: mise env prepends its tool bin dirs, and dropping
# the inherited PATH keeps stale entries (e.g. Homebrew's node) from shadowing them.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "${HOME}"
eval "$(mise env -s bash)"

if ! command -v skills >/dev/null 2>&1; then
  echo "skills not found on PATH; run 'mise install' first" >&2
  exit 1
fi

# --skill '*' installs every skill in the repo (caveman family plus
# investigate-first, lean-build, migration, safe-refactor, surgical-patch,
# verify-and-stop). Not --all: that implies --agent '*', but only the
# universal store may be targeted (see above).
echo "Adding skills: JuliusBrussee/caveman (all)"
skills add JuliusBrussee/caveman --skill '*' --agent universal -g -y

echo "Adding skills: github/gh-stack (gh-stack)"
skills add github/gh-stack --skill gh-stack --agent universal -g -y

echo "Adding skills: shadcn/improve (improve)"
skills add shadcn/improve --skill improve --agent universal -g -y
