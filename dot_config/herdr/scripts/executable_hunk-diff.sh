#!/bin/bash
# Open a hunk diff from the current herdr pane in a new tab or right split.
# Port of edmundmiller/herdr-plugin-hunk using the herdr CLI directly, so the
# actions stay under chezmoi management. Theme comes from hunk's own config.
# usage: hunk-diff.sh <worktree|staged|branch> <tab|split>
set -eu

mode="${1:-}"
target="${2:-}"
usage="usage: $(basename "$0") worktree|staged|branch tab|split"
case "$mode" in worktree | staged | branch) ;; *)
  echo "$usage" >&2
  exit 2
  ;;
esac
case "$target" in tab | split) ;; *)
  echo "$usage" >&2
  exit 2
  ;;
esac

# Use the context captured when the keybinding fired. A detached shell command
# may start after the user has focused another pane.
workspace_id="${HERDR_ACTIVE_WORKSPACE_ID:?HERDR_ACTIVE_WORKSPACE_ID is required}"
pane_id="${HERDR_ACTIVE_PANE_ID:?HERDR_ACTIVE_PANE_ID is required}"
tab_id="${HERDR_ACTIVE_TAB_ID:?HERDR_ACTIVE_TAB_ID is required}"
cwd="${HERDR_ACTIVE_PANE_CWD:-$PWD}"

# Panes are labeled per mode so a repeated press can tell "toggle this diff
# closed" apart from "switch to another diff".
case "$mode" in
worktree) pane_label="hunk" ;;
*) pane_label="hunk:$mode" ;;
esac

# Toggle/replace for splits: close any hunk pane already in this tab. Same
# mode means toggle off (stop here); another mode falls through and reopens.
if [ "$target" = "split" ]; then
  toggle_off=0
  closed_self=0
  while read -r open_pane open_label; do
    [ -n "$open_pane" ] || continue
    herdr pane close "$open_pane" >/dev/null
    [ "$open_label" = "$pane_label" ] && toggle_off=1
    [ "$open_pane" = "$pane_id" ] && closed_self=1
  done <<EOF
$(herdr pane list | jq -r --arg tab "$tab_id" '.result.panes[] | select(.tab_id == $tab) | select((.label // "") == "hunk" or ((.label // "") | startswith("hunk:"))) | "\(.pane_id) \(.label // "")"')
EOF
  [ "$toggle_off" = "1" ] && exit 0
  # Fired from inside a hunk pane that we just closed as part of a mode
  # switch — split from the pane that received focus instead.
  if [ "$closed_self" = "1" ]; then
    {
      read -r pane_id
      read -r cwd
    } <<EOF2
$(herdr pane current | jq -r '.result.pane | .pane_id, (.foreground_cwd // .cwd // ".")')
EOF2
  fi
fi

case "$mode" in
staged)
  hunk_cmd="hunk diff --staged"
  ;;
branch)
  # Whole-branch diff from the merge-base with the PR base branch (or the
  # default branch when no PR exists); resolution lives in branch-diff-cmd.sh.
  hunk_cmd="$(bash "$HOME/.config/herdr/scripts/branch-diff-cmd.sh" "$cwd")"
  ;;
*)
  hunk_cmd="hunk diff"
  ;;
esac

if [ "$target" = "tab" ]; then
  new_pane="$(herdr tab create --workspace "$workspace_id" --cwd "$cwd" --label hunk --focus |
    jq -r '.result.root_pane.pane_id')"
else
  new_pane="$(herdr pane split "$pane_id" --direction right --cwd "$cwd" --focus |
    jq -r '.result.pane.pane_id')"
fi

herdr pane rename "$new_pane" "$pane_label" >/dev/null
herdr pane run "$new_pane" "$hunk_cmd" >/dev/null
