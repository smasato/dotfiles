#!/bin/bash

set -eu

# Install global agent skills via the mise-managed `skills` CLI.
# Reruns when this list changes (e.g. when a skill is added below).
# skills: ChromeDevTools/chrome-devtools-mcp:*
# skills: JuliusBrussee/caveman:*
# pstack and control-cli/control-ui/deslop are maintained in dot_agents/skills.
# skills: emilkowalski/skill:*
# skills: github/gh-stack:gh-stack
# skills: mattpocock/skills:explicit list (tdd/teach are locally maintained pstack ports)
# skills: shadcn/improve:improve
# skills: shadcn/ui:*
# skills: vercel-labs/agent-browser:agent-browser
# skills: vercel-labs/skills:find-skills
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
echo "Adding skills: ChromeDevTools/chrome-devtools-mcp (all)"
skills add ChromeDevTools/chrome-devtools-mcp --skill '*' --agent universal -g -y

echo "Adding skills: JuliusBrussee/caveman (all)"
skills add JuliusBrussee/caveman --skill '*' --agent universal -g -y

echo "Adding skills: emilkowalski/skill (all)"
skills add emilkowalski/skill --skill '*' --agent universal -g -y

echo "Adding skills: github/gh-stack (gh-stack)"
skills add github/gh-stack --skill gh-stack --agent universal -g -y

# Explicit names keep upstream tdd/teach from overwriting the managed pstack ports.
echo "Adding skills: mattpocock/skills (excluding managed pstack names)"
skills add mattpocock/skills \
  --skill prototype --skill ask-matt --skill code-review --skill codebase-design \
  --skill diagnosing-bugs --skill domain-modeling --skill grill-with-docs \
  --skill implement --skill improve-codebase-architecture --skill research \
  --skill resolving-merge-conflicts --skill setup-matt-pocock-skills \
  --skill to-spec --skill to-tickets --skill triage --skill wayfinder --skill wizard \
  --skill claude-handoff --skill implement-spec --skill loop-me --skill retro \
  --skill setup-ts-deep-modules --skill writing-beats --skill writing-fragments \
  --skill writing-shape --skill git-guardrails-claude-code --skill migrate-to-shoehorn \
  --skill scaffold-exercises --skill setup-pre-commit --skill grill-me --skill grilling \
  --skill handoff --skill to-questionnaire --skill wait-what --skill writing-for-agents \
  --agent universal -g -y

# Cursor-origin workflows are deployed directly by chezmoi. See docs/pstack/README.md.

echo "Adding skills: shadcn/improve (improve)"
skills add shadcn/improve --skill improve --agent universal -g -y

echo "Adding skills: shadcn/ui (all)"
skills add shadcn/ui --skill '*' --agent universal -g -y

echo "Adding skills: vercel-labs/agent-browser (agent-browser)"
skills add vercel-labs/agent-browser --skill agent-browser --agent universal -g -y

echo "Adding skills: vercel-labs/skills (find-skills)"
skills add vercel-labs/skills --skill find-skills --agent universal -g -y
