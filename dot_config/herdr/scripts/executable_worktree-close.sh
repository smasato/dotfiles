#!/bin/bash
# Close the herdr workspace attached to a removed worktree.
# Called from worktrunk's post-remove hook, deferred through pueue so it runs
# in pueued's session instead of the pane where `wt remove` was invoked.
# Closing that workspace kills the pane's process group, which would otherwise
# take wt's own background cleanup (the rm -rf of .git/wt/trash) down with it
# and leave orphaned trash directories.
set -eu

worktree_path="$1"

workspaces=$(herdr workspace list)

# Closing a workspace moves herdr's focus to a neighbor even when the closed
# workspace is not the focused one; remember the focused workspace so it can
# be restored afterwards.
focused=$(jq -r '.result.workspaces[] | select(.focused) | .workspace_id' <<<"$workspaces")

jq -r --arg p "$worktree_path" \
  '.result.workspaces[] | select(.worktree.checkout_path == $p) | .workspace_id' \
  <<<"$workspaces" |
  while read -r ws; do
    [ -n "$ws" ] || continue
    herdr workspace close "$ws"
    # Restore focus immediately after each close to keep the window where the
    # neighbor workspace is shown as short as possible. Fails harmlessly when
    # the focused workspace was the one just closed.
    [ -z "$focused" ] || [ "$focused" = "$ws" ] ||
      herdr workspace focus "$focused" >/dev/null 2>&1 || true
  done
