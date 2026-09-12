#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title ​
# @raycast.mode inline
# @raycast.refreshTime 5m

# Optional parameters:
# @raycast.icon 🏢
# @raycast.packageName Claude Code

# Documentation:
# @raycast.description Show Claude subscription usage limits (work account, wclaude).
# @raycast.author smasato
# @raycast.authorURL https://raycast.com/smasato

# Fetch + format live in ~/.local/bin/claude-usage (shared with claude-usage and herdr).
"$HOME/.local/bin/claude-usage" --config-dir "$HOME/.claude_work" || {
    echo "usage unavailable"
    exit 1
}
