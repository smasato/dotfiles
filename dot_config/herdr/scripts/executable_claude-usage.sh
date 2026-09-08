#!/bin/bash

# Compact Claude usage line for the herdr tab bar (ui.tab_bar_right command entry).
# Fetch + format live in ~/.local/bin/claude-usage (shared with the Raycast
# scripts); --compact drops the alignment padding to fit the tab bar. Exits
# non-zero on failure so herdr hides the entry.

exec "$HOME/.local/bin/claude-usage" --config-dir "$HOME/.claude" --compact
