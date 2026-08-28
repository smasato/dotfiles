#!/bin/bash

set -eu

# Install global agent skills via the mise-managed `skills` CLI.
# Reruns when this list changes (e.g. when a skill is added below).
# skills: ChromeDevTools/chrome-devtools-mcp:*
# skills: JuliusBrussee/caveman:*
# skills: cursor/plugins:pstack (all except setup-pstack) + control-cli/control-ui/deslop
# skills: emilkowalski/skill:*
# skills: github/gh-stack:gh-stack
# skills: mattpocock/skills:*
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

echo "Adding skills: mattpocock/skills (all)"
skills add mattpocock/skills --skill '*' --agent universal -g -y

# pstack (https://github.com/cursor/plugins/tree/main/pstack) plus the three
# cursor-team-kit skills poteto-mode invokes as hard steps (deslop,
# control-cli, control-ui). The skills CLI matches frontmatter names, so
# "Poteto Mode" and "Make Bot UI" are display names, not slugs. This block
# must run after mattpocock/skills: both repos ship tdd and teach under the
# same flat names, installs overwrite, and the pstack versions are the ones
# that should win. setup-pstack is excluded: it writes ~/.cursor/rules/,
# which Claude Code never reads; the pstack model mapping lives in
# dot_claude/rules/pstack-models.md instead.
echo "Adding skills: cursor/plugins (pstack + team-kit subset)"
skills add cursor/plugins \
  --skill architect --skill arena --skill automate-me --skill blast-radius --skill bro \
  --skill create-verification-skill --skill figure-it-out --skill how --skill interrogate \
  --skill maintain-verification-skill --skill "Make Bot UI" --skill no-comments --skill "Poteto Mode" \
  --skill principle-boundary-discipline --skill principle-build-the-lever \
  --skill principle-encode-lessons-in-structure --skill principle-exhaust-the-design-space \
  --skill principle-experience-first --skill principle-fix-root-causes \
  --skill principle-foundational-thinking --skill principle-guard-the-context-window \
  --skill principle-laziness-protocol --skill principle-make-operations-idempotent \
  --skill principle-migrate-callers-then-delete-legacy-apis --skill principle-minimize-reader-load \
  --skill principle-model-the-domain --skill principle-never-block-on-the-human \
  --skill principle-outcome-oriented-execution --skill principle-prove-it-works \
  --skill principle-redesign-from-first-principles --skill principle-separate-before-serializing-shared-state \
  --skill principle-sequence-verifiable-units --skill principle-subtract-before-you-add \
  --skill principle-type-system-discipline --skill recall --skill reflect \
  --skill show-me-your-work --skill swarm --skill tdd --skill teach \
  --skill technical-writing --skill typescript-best-practices \
  --skill unslop --skill why \
  --skill deslop --skill control-cli --skill control-ui \
  --agent universal -g -y

echo "Adding skills: shadcn/improve (improve)"
skills add shadcn/improve --skill improve --agent universal -g -y

echo "Adding skills: shadcn/ui (all)"
skills add shadcn/ui --skill '*' --agent universal -g -y

echo "Adding skills: vercel-labs/agent-browser (agent-browser)"
skills add vercel-labs/agent-browser --skill agent-browser --agent universal -g -y

echo "Adding skills: vercel-labs/skills (find-skills)"
skills add vercel-labs/skills --skill find-skills --agent universal -g -y
