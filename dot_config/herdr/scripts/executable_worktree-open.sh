#!/bin/bash
# Open a worktree in herdr and lay out the workspace:
#   tab 1: shell (left) + file viewer (right)
#   tab 2: lazygit (tab label "lazygit", matching scripts/lazygit-tab.sh)
#   tab 3: shell (left) + yazi (right) (tab label "yazi")
# Hunk diff tabs are not part of the layout; open them on demand via
# hunk-diff.sh.
# Called from worktrunk's post-switch hook with the repo path, worktree path,
# and branch. The layout is only built while the workspace is still bare (a
# single pane) so re-running the hook against a laid-out workspace doesn't
# stack extra panes or tabs. The pane count is the guard rather than the
# `already_open` flag from `worktree open`: the herdr worktrunk plugin picker
# registers the workspace itself right after `wt switch` returns, so this hook
# often finds the workspace already open but not yet laid out.
#
# The viewer split targets the workspace's initial shell pane explicitly
# (`--target-pane`) instead of invoking the plugin's open-file-viewer action,
# which operates on the *focused* pane and would race with the user switching
# workspaces while the hook runs. `plugin pane open` must not be given --cwd:
# the pane command is a relative path resolved against the plugin root, and the
# viewer roots its tree from the workspace cwd herdr injects via
# HERDR_PLUGIN_CONTEXT_JSON, not the process cwd.
# Open and lay out with --no-focus so creating a worktree does not steal the
# current workspace. The worktrunk picker focuses afterwards when the user
# picks one; a plain `wt switch` from a shell does not.
set -eu

repo_path="$1"
worktree_path="$2"
branch="$3"

out="$(herdr worktree open --cwd "$repo_path" --path "$worktree_path" --label "$branch" --no-focus)"

ws="$(printf '%s' "$out" | jq -r '.result.workspace.workspace_id // empty')"
[ -n "$ws" ] || exit 0

# The workspace's initial shell pane can appear slightly after worktree open
# returns; poll briefly for it.
panes='[]'
for _ in 1 2 3 4 5 6 7 8 9 10; do
  panes="$(herdr pane list --workspace "$ws" 2>/dev/null | jq -c '.result.panes // []')"
  [ "$(printf '%s' "$panes" | jq 'length')" -gt 0 ] && break
  sleep 0.2
done

# Bare workspace has exactly the initial shell pane; more means the layout is
# already built.
[ "$(printf '%s' "$panes" | jq 'length')" = 1 ] || exit 0
pane="$(printf '%s' "$panes" | jq -r '.[0].pane_id // empty')"
[ -n "$pane" ] || exit 0

# Keep focus on the shell pane; the viewer opens beside it unfocused.
herdr plugin pane open \
  --plugin herdr-file-viewer \
  --entrypoint file-viewer \
  --placement split \
  --direction right \
  --target-pane "$pane" \
  --no-focus >/dev/null

# Tab 2: lazygit via the plugin's tab entrypoint (pane label "Git" comes from
# the plugin manifest); pin the tab label to "lazygit" like lazygit-tab.sh.
lazygit_tab="$(herdr plugin pane open \
  --plugin herdr-lazygit \
  --entrypoint lazygit \
  --placement tab \
  --workspace "$ws" \
  --cwd "$worktree_path" \
  --no-focus | jq -r '.result.plugin_pane.pane.tab_id // empty')"
[ -n "$lazygit_tab" ] && herdr tab rename "$lazygit_tab" lazygit >/dev/null

# Tab 3: shell (left) + yazi (right); the tab's initial pane stays a plain
# shell and yazi runs in the split.
yazi_shell_pane="$(herdr tab create --workspace "$ws" --cwd "$worktree_path" --label yazi --no-focus |
  jq -r '.result.root_pane.pane_id // empty')"
if [ -n "$yazi_shell_pane" ]; then
  yazi_pane="$(herdr pane split "$yazi_shell_pane" --direction right --cwd "$worktree_path" --no-focus |
    jq -r '.result.pane.pane_id // empty')"
  if [ -n "$yazi_pane" ]; then
    herdr pane rename "$yazi_pane" yazi >/dev/null
    herdr pane run "$yazi_pane" yazi >/dev/null
  fi
fi
