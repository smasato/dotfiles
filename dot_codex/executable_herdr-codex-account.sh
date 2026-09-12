#!/bin/sh
# Keep the hook command stable across CODEX_HOME symlinks and existing hooks.json.
# Async execution belongs to Codex, not to a detached child of this script.
exec python3 "$(dirname "$0")/herdr-codex-account.py" "$@"
