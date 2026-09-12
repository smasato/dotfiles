#!/bin/bash
# Capture before removal, then queue an identity-bound close after removal.
# The actual close runs in pueued's process group, preserving wt trash cleanup.
set -eu
exec python3 "$(dirname "$0")/worktree.py" "$@"
