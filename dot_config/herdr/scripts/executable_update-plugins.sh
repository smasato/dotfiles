#!/bin/bash
# Shared installer for chezmoi apply and the repository update task.
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "$HOME"
eval "$(mise env -s bash)"
exec python3 "$script_dir/herdr_plugins.py"
