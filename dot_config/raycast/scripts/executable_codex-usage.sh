#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title ​
# @raycast.mode inline
# @raycast.refreshTime 5m

# Optional parameters:
# @raycast.icon 🧠
# @raycast.packageName Codex

# Documentation:
# @raycast.description Show Codex (ChatGPT) subscription usage limits.
# @raycast.author smasato
# @raycast.authorURL https://raycast.com/smasato

# Fetch + format live in ~/.local/bin/codex-usage (same shape as claude-usage).
"$HOME/.local/bin/codex-usage" || {
    echo "usage unavailable"
    exit 1
}
