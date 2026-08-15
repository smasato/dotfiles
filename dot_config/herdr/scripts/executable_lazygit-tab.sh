#!/bin/bash
# Open (or switch to) the herdr-lazygit tab via the plugin action and pin the
# tab label to "lazygit" — herdr labels tabs with bare numbers and the plugin
# offers no way to name the tab it creates. When the lazygit tab is already
# focused, jump back to the tab we came from (remembered per workspace)
# instead of letting the plugin toggle the pane closed; close the tab with
# lazygit's own quit (q) or close_tab instead.
set -eu

state_dir="${TMPDIR:-/tmp}/herdr-lazygit-return"
mkdir -p "$state_dir"

# Use the context captured when the keybinding fired. A detached shell command
# may start after the user has focused another pane.
workspace_id="${HERDR_ACTIVE_WORKSPACE_ID:?HERDR_ACTIVE_WORKSPACE_ID is required}"
pane_id="${HERDR_ACTIVE_PANE_ID:?HERDR_ACTIVE_PANE_ID is required}"
tab_id="${HERDR_ACTIVE_TAB_ID:?HERDR_ACTIVE_TAB_ID is required}"
cwd="${HERDR_ACTIVE_PANE_CWD:-$PWD}"

label="$(herdr tab get "$tab_id" | jq -r '.result.tab.label // ""')"
mode="OPEN"
[ "$label" = "lazygit" ] && mode="RETURN"

state_file="$state_dir/$(printf '%s' "$workspace_id" | tr -c 'A-Za-z0-9_-' '_')"

if [ "$mode" = "RETURN" ]; then
  back=""
  [ -f "$state_file" ] && back="$(cat "$state_file")"
  if [ -n "$back" ] && herdr tab focus "$back" >/dev/null 2>&1; then
    exit 0
  fi
  # The recorded tab is gone — fall back to the lowest-numbered other tab in
  # this workspace, or stay put if the lazygit tab is the only one.
  fallback="$(herdr tab list 2>/dev/null | jq -r --arg ws "$workspace_id" --arg cur "$tab_id" '[.result.tabs[] | select(.workspace_id == $ws and .tab_id != $cur)] | sort_by(.number) | .[0].tab_id // ""' 2>/dev/null || true)"
  [ -n "$fallback" ] && exec herdr tab focus "$fallback"
  exit 0
fi

# Remember where we came from so the next press on the lazygit tab returns here.
printf '%s\n' "$tab_id" >"$state_file"

HERDR_WORKSPACE_ID="$workspace_id" \
  HERDR_TAB_ID="$tab_id" \
  HERDR_PANE_ID="$pane_id" \
  HERDR_ACTIVE_PANE_CWD="$cwd" \
  herdr plugin action invoke open-tab --plugin herdr-lazygit

# The pane opens asynchronously; poll briefly for "Git" panes that are the
# only pane in their tab (the tab variant — split lazygit panes share a tab
# with other panes). On the toggle-close path nothing matches and we time out.
for _ in 1 2 3 4 5 6 7 8 9 10; do
  tab_ids="$(herdr pane list 2>/dev/null | jq -r '
    .result.panes as $panes
    | reduce $panes[] as $p ({}; .[$p.tab_id] += 1) as $counts
    | $panes[] | select(.label == "Git" and $counts[.tab_id] == 1) | .tab_id
  ' 2>/dev/null || true)"
  if [ -n "${tab_ids}" ]; then
    for tab_id in ${tab_ids}; do
      herdr tab rename "${tab_id}" lazygit >/dev/null 2>&1 || true
    done
    exit 0
  fi
  sleep 0.2
done
