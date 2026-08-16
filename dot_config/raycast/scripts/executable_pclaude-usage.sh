#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Claude
# @raycast.mode inline
# @raycast.refreshTime 15m

# Optional parameters:
# @raycast.icon 🏠
# @raycast.packageName Claude Code

# Documentation:
# @raycast.description Show Claude subscription usage limits (personal config, pclaude).
# @raycast.author smasato
# @raycast.authorURL https://raycast.com/smasato

CLAUDE="$HOME/.local/share/mise/installs/claude-code/latest/claude"

if [ ! -x "$CLAUDE" ]; then
    echo "claude binary not found: $CLAUDE"
    exit 1
fi

output=$(CLAUDE_CONFIG_DIR="$HOME/.claude_personal_home" "$CLAUDE" -p /usage 2>&1)

parsed=$(echo "$output" | grep '^Current' | sed -E \
    -e 's/^Current session: ([0-9]+%) used · resets (.+) \(.*\)$/S \1 (\2)/' \
    -e 's/^Current week \(all models\): ([0-9]+%) used · resets (.+) \(.*\)$/W \1 (\2)/' \
    -e 's/^Current week \(([^)]+)\): ([0-9]+%) used · resets (.+) \(.*\)$/\1 \2 (\3)/' \
    -e 's/ at / /g' \
    | perl -pe 'BEGIN{%m=(Jan=>1,Feb=>2,Mar=>3,Apr=>4,May=>5,Jun=>6,Jul=>7,Aug=>8,Sep=>9,Oct=>10,Nov=>11,Dec=>12)} s{\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b}{sprintf("%02d/%02d", $m{$1}, $2)}ge; s{\b(\d{1,2})(?::(\d{2}))?(am|pm)\b}{sprintf("%d:%02d", ($1 % 12) + ($3 eq "pm" ? 12 : 0), defined $2 ? $2 : 0)}ge; s{(\d+)%}{($1 >= 90 ? "🔴" : $1 >= 70 ? "🟡" : "🔵") . " $1%"}ge' \
    | awk '{printf "%s%s", sep, $0; sep=" · "} END {print ""}')

if [ -z "$parsed" ]; then
    echo "usage unavailable"
    exit 1
fi

echo "$parsed"
