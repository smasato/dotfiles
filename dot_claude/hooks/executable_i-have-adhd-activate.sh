#!/bin/sh
# SessionStart hook: emit the i-have-adhd SKILL.md ruleset as session context
# so it applies to every response without relying on skill auto-triggering.
# The plugin cache path contains a commit hash segment that changes when the
# plugin updates, so resolve it with a glob and take the newest match.
set -eu

skill=$(ls -td "$HOME"/.claude/plugins/cache/i-have-adhd/i-have-adhd/*/skills/i-have-adhd/SKILL.md 2>/dev/null | head -n 1)
[ -n "$skill" ] || exit 0

echo "I-HAVE-ADHD MODE ACTIVE — apply these rules to every response:"
# Strip the YAML frontmatter; only the ruleset body goes into context.
awk 'NR==1 && /^---$/ {fm=1; next} fm==1 {if (/^---$/) fm=2; next} {print}' "$skill"
