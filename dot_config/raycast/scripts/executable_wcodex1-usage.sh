#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title ​
# @raycast.mode inline
# @raycast.refreshTime 5m

# Optional parameters:
# @raycast.icon 1️⃣
# @raycast.packageName Codex

# Documentation:
# @raycast.description Show Codex (ChatGPT) subscription usage limits (work seat 1, wcodex1).
# @raycast.author smasato
# @raycast.authorURL https://raycast.com/smasato

# Fetch + format live in ~/.local/bin/codex-usage (shared with codex-usage and herdr).
"$HOME/.local/bin/codex-usage" --codex-home "$HOME/.codex_work1" || {
    echo "usage unavailable"
    exit 1
}
