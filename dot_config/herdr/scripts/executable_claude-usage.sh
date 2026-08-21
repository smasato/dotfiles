#!/bin/bash

# Compact Claude usage line for the herdr tab bar (ui.tab_bar_right command entry).
# Same /usage source as the Raycast scripts, but drops reset times and padding
# to fit the tab bar. Exit non-zero on failure so herdr hides the entry.

CLAUDE="$HOME/.local/share/mise/installs/claude-code/latest/claude"

if [ ! -x "$CLAUDE" ]; then
    exit 1
fi

output=$(env -u CLAUDE_CONFIG_DIR "$CLAUDE" -p /usage 2>&1)

parsed=$(echo "$output" | grep '^Current' | sed -E \
    -e 's/^Current session: ([0-9]+%) used.*$/S \1/' \
    -e 's/^Current week \(all models\): ([0-9]+%) used.*$/W \1/' \
    -e 's/^Current week \(([^)]+)\): ([0-9]+%) used.*$/\1 \2/' \
    | perl -pe 's{ (\d+)%}{($1 >= 90 ? "🔴" : $1 >= 75 ? "🟡" : "🔵") . "$1%"}ge' \
    | awk '{printf "%s%s", sep, $0; sep=" "} END {print ""}')

if [ -z "$parsed" ]; then
    exit 1
fi

echo "$parsed"
