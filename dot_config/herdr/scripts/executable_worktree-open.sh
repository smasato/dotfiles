#!/bin/bash
# Open a worktree in herdr and lay out the workspace:
#   tab 1: shell (left) + file viewer (right)
#   tab 2: lazygit (tab label "lazygit", matching scripts/lazygit-tab.sh)
#   tab 3: hunk diffs (tab label "hunk") — left pane: working tree incl.
#          unstaged (pane label "hunk"), right pane: whole-branch diff from
#          the merge-base with the PR base / default branch (pane label
#          "hunk:branch"); labels match hunk-diff.sh so its toggle logic
#          recognizes both panes
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
set -eu

repo_path="$1"
worktree_path="$2"
branch="$3"

out="$(herdr worktree open --cwd "$repo_path" --path "$worktree_path" --label "$branch" --focus --json)"

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

# Tab 3: hunk diffs — left pane shows the working tree incl. unstaged changes
# (`hunk diff`, label "hunk"), right pane shows the whole branch from the
# merge-base with its PR base branch or the default branch (label
# "hunk:branch"); resolution lives in branch-diff-cmd.sh, shared with
# hunk-diff.sh.
hunk_pane="$(herdr tab create --workspace "$ws" --cwd "$worktree_path" --label hunk --no-focus |
  jq -r '.result.root_pane.pane_id // empty')"
if [ -n "$hunk_pane" ]; then
  herdr pane rename "$hunk_pane" hunk >/dev/null
  herdr pane run "$hunk_pane" "hunk diff" >/dev/null

  branch_pane="$(herdr pane split "$hunk_pane" --direction right --cwd "$worktree_path" --no-focus |
    jq -r '.result.pane.pane_id // empty')"
  if [ -n "$branch_pane" ]; then
    herdr pane rename "$branch_pane" "hunk:branch" >/dev/null
    herdr pane run "$branch_pane" "$(bash "$HOME/.config/herdr/scripts/branch-diff-cmd.sh" "$worktree_path")" >/dev/null
  fi
fi

# Land the user on tab 1's shell: the viewer split can steal in-tab focus even
# with --no-focus. herdr has no focus-by-id, so focus via a zoom on/off cycle
# (--on focuses and maximizes, --off un-maximizes keeping focus) — the same
# trick the file-viewer plugin's own launcher uses.
herdr pane zoom "$pane" --on >/dev/null 2>&1 || true
herdr pane zoom "$pane" --off >/dev/null 2>&1 || true
