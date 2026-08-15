#!/bin/bash
# Close the herdr workspace attached to a removed worktree.
# Called from worktrunk's post-remove hook, deferred through pueue so it runs
# in pueued's session instead of the pane where `wt remove` was invoked.
# Closing that workspace kills the pane's process group, which would otherwise
# take wt's own background cleanup (the rm -rf of .git/wt/trash) down with it
# and leave orphaned trash directories.
set -eu

worktree_path="$1"

herdr workspace list |
  jq -r --arg p "$worktree_path" \
    '.result.workspaces[] | select(.worktree.checkout_path == $p) | .workspace_id' |
  while read -r ws; do
    [ -n "$ws" ] || continue
    herdr workspace close "$ws"
  done
