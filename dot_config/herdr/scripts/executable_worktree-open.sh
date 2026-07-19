#!/bin/bash
# Open a worktree in herdr and lay out the workspace:
#   tab 1: shell (left) + file viewer (right)
#   tab 2: lazygit (tab label "lazygit", matching scripts/lazygit-tab.sh)
#   tab 3: hunk diffs (tab label "hunk") — left pane: working tree incl.
#          unstaged (pane label "hunk"), right pane: whole-branch diff against
#          upstream (pane label "hunk:branch"); labels match hunk-diff.sh so
#          its toggle logic recognizes both panes
# Called from worktrunk's post-start hook with the repo path, worktree path,
# and branch. The layout is only built when the workspace is newly created
# (`already_open` false) so re-running the hook against an existing workspace
# doesn't stack extra panes or tabs.
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
already_open="$(printf '%s' "$out" | jq -r '.result.already_open // false')"
[ -n "$ws" ] || exit 0
[ "$already_open" = "false" ] || exit 0

# The workspace's initial shell pane can appear slightly after worktree open
# returns; poll briefly for it.
pane=""
for _ in 1 2 3 4 5 6 7 8 9 10; do
  pane="$(herdr pane list --workspace "$ws" 2>/dev/null | jq -r '.result.panes[0].pane_id // empty')"
  [ -n "$pane" ] && break
  sleep 0.2
done
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
# (`hunk diff`, label "hunk"), right pane shows the whole branch against its
# upstream (label "hunk:branch"). Upstream detection mirrors hunk-diff.sh:
# @{upstream} first, then the usual default-branch candidates.
hunk_pane="$(herdr tab create --workspace "$ws" --cwd "$worktree_path" --label hunk --no-focus |
  jq -r '.result.root_pane.pane_id // empty')"
if [ -n "$hunk_pane" ]; then
  herdr pane rename "$hunk_pane" hunk >/dev/null
  herdr pane run "$hunk_pane" "hunk diff" >/dev/null

  upstream="$(git -C "$worktree_path" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)"
  if [ -z "$upstream" ]; then
    for candidate in origin/main origin/master main master; do
      if git -C "$worktree_path" rev-parse --verify --quiet "$candidate" >/dev/null 2>&1; then
        upstream="$candidate"
        break
      fi
    done
  fi
  [ -n "$upstream" ] || upstream=origin/main

  branch_pane="$(herdr pane split "$hunk_pane" --direction right --cwd "$worktree_path" --no-focus |
    jq -r '.result.pane.pane_id // empty')"
  if [ -n "$branch_pane" ]; then
    herdr pane rename "$branch_pane" "hunk:branch" >/dev/null
    herdr pane run "$branch_pane" "$(printf 'hunk diff %q..%q' "$upstream" "$branch")" >/dev/null
  fi
fi

# Land the user on tab 1's shell: the viewer split can steal in-tab focus even
# with --no-focus. herdr has no focus-by-id, so focus via a zoom on/off cycle
# (--on focuses and maximizes, --off un-maximizes keeping focus) — the same
# trick the file-viewer plugin's own launcher uses.
herdr pane zoom "$pane" --on >/dev/null 2>&1 || true
herdr pane zoom "$pane" --off >/dev/null 2>&1 || true
