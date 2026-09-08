#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title ​
# @raycast.mode inline
# @raycast.refreshTime 5m

# Optional parameters:
# @raycast.icon 🏠
# @raycast.packageName Claude Code

# Documentation:
# @raycast.description Show Claude subscription usage limits (personal config, pclaude).
# @raycast.author smasato
# @raycast.authorURL https://raycast.com/smasato

# Fetch + format live in ~/.local/bin/claude-usage (shared with claude-usage and herdr).
"$HOME/.local/bin/claude-usage" --config-dir "$HOME/.claude_personal_home" || {
    echo "usage unavailable"
    exit 1
}
