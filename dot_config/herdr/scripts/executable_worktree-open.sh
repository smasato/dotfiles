#!/bin/bash
# Serialize and resume the standard shell/viewer, lazygit, shell/yazi layout.
# Completed or customized workspaces stay unchanged; never steal focus.
set -eu
exec python3 "$(dirname "$0")/worktree.py" open "$@"
