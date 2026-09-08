#!/bin/bash

# Compact Codex usage line for the herdr tab bar (ui.tab_bar_right command entry).
# Fetch + format live in ~/.local/bin/codex-usage (shared with the Raycast
# script); --compact drops the alignment padding to fit the tab bar. The
# "Cx" prefix tells it apart from the Claude entry next to it. Exits
# non-zero on failure so herdr hides the entry.

line=$("$HOME/.local/bin/codex-usage" --compact) || exit 1
echo "Cx $line"
