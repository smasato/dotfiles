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

# Context of the pane the keybinding fired in. cwd is read as a full line so
# paths with spaces survive.
{
  read -r workspace_id
  read -r pane_id
  read -r tab_id
  read -r cwd
} <<EOF
$(herdr pane current | python3 -c '
import json, sys
p = json.load(sys.stdin)["result"]["pane"]
print(p["workspace_id"])
print(p["pane_id"])
print(p["tab_id"])
print(p.get("foreground_cwd") or p.get("cwd") or ".")
')
EOF

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
$(herdr pane list | HUNK_TAB="$tab_id" python3 -c '
import json, os, sys
panes = json.load(sys.stdin)["result"]["panes"]
for p in panes:
    if not isinstance(p, dict) or p.get("tab_id") != os.environ["HUNK_TAB"]:
        continue
    label = p.get("label") or ""
    if label == "hunk" or label.startswith("hunk:"):
        print(p["pane_id"], label)
')
EOF
  [ "$toggle_off" = "1" ] && exit 0
  # Fired from inside a hunk pane that we just closed as part of a mode
  # switch — split from the pane that received focus instead.
  if [ "$closed_self" = "1" ]; then
    {
      read -r pane_id
      read -r cwd
    } <<EOF2
$(herdr pane current | python3 -c '
import json, sys
p = json.load(sys.stdin)["result"]["pane"]
print(p["pane_id"])
print(p.get("foreground_cwd") or p.get("cwd") or ".")
')
EOF2
  fi
fi

case "$mode" in
staged)
  hunk_cmd="hunk diff --staged"
  ;;
branch)
  branch="$(git -C "$cwd" branch --show-current 2>/dev/null || true)"
  [ -n "$branch" ] || branch=HEAD
  upstream="$(git -C "$cwd" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)"
  if [ -z "$upstream" ]; then
    for candidate in origin/main origin/master main master; do
      if git -C "$cwd" rev-parse --verify --quiet "$candidate" >/dev/null 2>&1; then
        upstream="$candidate"
        break
      fi
    done
  fi
  [ -n "$upstream" ] || upstream=origin/main
  hunk_cmd="$(printf 'hunk diff %q..%q' "$upstream" "$branch")"
  ;;
*)
  hunk_cmd="hunk diff"
  ;;
esac

if [ "$target" = "tab" ]; then
  new_pane="$(herdr tab create --workspace "$workspace_id" --cwd "$cwd" --label hunk --focus |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')"
else
  new_pane="$(herdr pane split "$pane_id" --direction right --cwd "$cwd" --focus |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')"
fi

herdr pane rename "$new_pane" "$pane_label" >/dev/null
herdr pane run "$new_pane" "$hunk_cmd" >/dev/null
