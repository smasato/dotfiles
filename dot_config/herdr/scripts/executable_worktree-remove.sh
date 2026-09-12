#!/bin/bash
# Confirm one checkout removal. Worktrunk lifecycle hooks own Herdr cleanup.
set -euo pipefail

fail() {
    printf '\n%s\n' "$1" >&2
    read -r -p 'Press Enter to close.' _ || true
    exit 1
}

for tool in wt jq fzf; do
    command -v "$tool" >/dev/null || fail "Missing command: $tool"
done

snapshot=$(wt list --format=json) || fail 'Cannot list worktrees.'
jq -e '.schema == 2 and (.items | type == "array")' <<< "$snapshot" >/dev/null ||
    fail 'Unsupported Worktrunk list response.'
primary=$(jq -er '.items[] | select(.worktree.main == true) | .worktree.path' <<< "$snapshot") ||
    fail 'Cannot find the primary worktree.'
# Keep the popup process outside a checkout that it may remove.
cd -- "$primary" || fail 'Cannot enter the primary worktree.'
candidates=$(jq -c '[.items[] | select(.worktree.main == false and
    .worktree.detached == false and .branch != null)]' <<< "$snapshot")
[[ "$candidates" != '[]' ]] || fail 'No removable worktrees (primary and detached are excluded).'
rows=$(jq -r 'to_entries[] | [.key, .value.branch, (.value.worktree.path | tojson)] | @tsv' <<< "$candidates")
selection=$(printf '%s\n' "$rows" | fzf --delimiter=$'\t' --with-nth=2.. \
    --no-multi --no-select-1 --no-exit-0 --reverse --border=none --margin=0 \
    --prompt='Remove worktree> ' --header='Enter: review removal / Esc: cancel') || {
    status=$?
    [[ "$status" == 1 || "$status" == 130 ]] && exit 0
    fail 'Worktree picker failed.'
}
index=${selection%%$'\t'*}
[[ "$index" =~ ^[0-9]+$ ]] || fail 'Invalid worktree selection.'
target=$(jq -ce --argjson index "$index" '.[$index] // empty' <<< "$candidates") ||
    fail 'Invalid worktree selection.'
# JSON quoting keeps control characters in paths out of terminal output.
jq -r '"Branch: " + (.branch | tojson), "Path:   " + (.worktree.path | tojson)' <<< "$target"
printf '\nRemove this checkout, including ignored files?\nMerged branches are deleted; unmerged branches are kept.\n'
read -r -p 'Remove? [y/N] ' answer || exit 0
case "$answer" in y|Y|yes|YES) ;; *) exit 0 ;; esac

latest=$(wt list --format=json) || fail 'Cannot recheck the selected worktree.'
jq -e --argjson target "$target" '.schema == 2 and any(.items[];
    .branch == $target.branch and .worktree.path == $target.worktree.path and
    .head.sha == $target.head.sha and .worktree.main == false and .worktree.detached == false)' \
    <<< "$latest" >/dev/null || fail 'Worktree changed while confirming; reopen the picker.'
# A sentinel preserves trailing newlines through command substitution.
path=$(jq -r '.worktree.path + "."' <<< "$target")
path=${path%.}
wt remove --foreground -- "$path" || fail 'Removal failed. Review the Worktrunk error above.'
