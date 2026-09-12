#!/usr/bin/env bash
# Read-only worktree prune audit. Classifies every git worktree by size, merge
# state, uncommitted work, remote/PR state, and the most recent chat that
# operated in it. Emits a table sorted by size with a suggested bucket. Never
# deletes anything; deletion stays a human-gated step in the playbook.
#
# Usage: worktree-audit.sh [repo-path] [scoped-transcript-directory]
set -u
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

repo="${1:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$repo" ] && { echo "not in a git repo; pass a repo path" >&2; exit 1; }
cd "$repo" || exit 1

worktrees=$(mktemp)
prs=$(mktemp)
prune=$(mktemp)
herdr_snapshot=$(mktemp)
herdr_paths=$(mktemp)
trap 'rm -f "$worktrees" "$prs" "$prune" "$herdr_snapshot" "$herdr_paths"' EXIT
wt list --format=json > "$worktrees" || exit 1
jq -e '.schema == 2 and (.items | type == "array")' "$worktrees" >/dev/null || exit 1
main_wt=$(jq -r '.items[] | select(.worktree.main == true) | .worktree.path' "$worktrees")
trunk=$(jq -r '.repo.default_branch' "$worktrees")

# This is only a preview. Its candidates do not override chat/WIP/PR checks.
# Unlike wt list's envelope, prune emits a JSON array, including branch-only rows.
prune_status=unknown
if wt step prune --dry-run --min-age=2d --format=json > "$prune" \
	&& jq -e 'type == "array"' "$prune" >/dev/null; then
	prune_status=available
else
	printf 'Prune preview unavailable; PRUNE is unknown. Continuing the audit.\n' >&2
fi

# PR state uses upstream repository, branch, and HEAD. Missing/ambiguous identity
# and lookup failures remain unknown; a same-named branch is not enough.
if ! python3 "$script_dir/worktree-prs.py" "$worktrees" > "$prs"; then
	printf '{}\n' > "$prs"
	printf 'PR lookup unavailable; PR is unknown.\n' >&2
fi

# Inspect only the current Herdr session when invoked from a Herdr pane.
# Map canonical paths once; a missing server/snapshot stays unknown, not closed.
if [ "${HERDR_ENV:-}" = 1 ] && herdr api snapshot > "$herdr_snapshot" 2>/dev/null \
	&& jq -e '.ok != false and (.result.snapshot.workspaces | type == "array")' "$herdr_snapshot" >/dev/null; then
	python3 - "$worktrees" "$herdr_snapshot" > "$herdr_paths" <<'PY'
import json, os, sys
worktrees = json.load(open(sys.argv[1]))
snapshot = json.load(open(sys.argv[2]))["result"]["snapshot"]
opened = {}
for workspace in snapshot["workspaces"]:
    path = (workspace.get("worktree") or {}).get("checkout_path")
    if path:
        opened.setdefault(os.path.realpath(path), []).append(workspace["workspace_id"])
print(json.dumps({item["worktree"]["path"]: ",".join(opened.get(os.path.realpath(item["worktree"]["path"]), [])) or "-"
                  for item in worktrees["items"] if item.get("worktree")}))
PY
fi

transcripts="${2:-}"
# Use macOS date/stat explicitly; GNU coreutils may precede them on PATH.
now=$(/bin/date +%s)

printf "SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tPRUNE\tHERDR\tMARKER\tBUCKET\tWORKTREE\n"

jq -c '.items[] | select(.worktree != null)' "$worktrees" | while IFS= read -r item; do
	wt=$(jq -r '.worktree.path' <<<"$item")
	[ "$wt" = "$main_wt" ] && continue

	size=$(du -sh "$wt" 2>/dev/null | awk '{print $1}')
	head=$(jq -r '.head.sha // empty' <<<"$item")
	head_ts=$(jq -r 'try (.head.committed_at | fromdateiso8601) catch 0' <<<"$item")
	age=$([ "$head_ts" -gt 0 ] 2>/dev/null && echo "$(( (now - head_ts) / 86400 ))d" || echo "?")

	# Squash-merged branches are not ancestors of main, so PR state is the
	# real signal; merge-base only catches fast-forward/rebase merges.
	merged=unknown
	if [ -n "$head" ] && [ "$trunk" != null ]; then
		git merge-base --is-ancestor "$head" "$trunk" 2>/dev/null
		case $? in 0) merged=YES ;; 1) merged=no ;; esac
	fi

	# Distinguish real WIP (tracked edits) from disposable untracked scratch.
	if ! porcelain=$(git -C "$wt" status --porcelain 2>/dev/null); then dirty=unknown
	elif [ -z "$porcelain" ]; then dirty=clean
	elif printf '%s\n' "$porcelain" | grep -qv '^??'; then
		dirty="wip:$(printf '%s\n' "$porcelain" | grep -cv '^??')"
	else dirty="scratch:$(printf '%s\n' "$porcelain" | grep -c '^??')"; fi

	remote=$(jq -r '
		if .worktree.detached then "detached"
		elif .branch == null then "unknown"
		elif .upstream == null then "no-upstream"
		elif (.upstream.ahead | type) != "number" or (.upstream.behind | type) != "number" then "unknown"
		else .upstream | "\(.remote)/\(.branch):+\(.ahead)/-\(.behind)" end' <<<"$item")

	pr=$(jq -r --arg p "$wt" '.[$p] // "unknown"' "$prs")
	# Saved activity is a hint, not process liveness or cleanup authorization.
	marker=$(jq -r 'if .marker == null or .marker == "" then "-"
		elif (.marker | type) == "string" then .marker | gsub("[\\t\\r\\n]"; " ")
		else "unknown" end' <<<"$item")
	herdr_state=$(jq -r --arg p "$wt" '.[$p] // "unknown"' "$herdr_paths" 2>/dev/null)
	[ -n "$herdr_state" ] || herdr_state=unknown

	# Most recent chat whose transcript operated in this worktree. Match path
	# followed by "/" or a quote so glint-482 does not match glint-482-r37.
	last="-"; last_ts=0
	if [ -d "$transcripts" ]; then
		f=$(rg -l -0 -F -e "${wt}/" -e "${wt}\"" "$transcripts" 2>/dev/null \
			| xargs -0 /usr/bin/stat -f '%m %N' 2>/dev/null | sort -rn | head -1)
		if [ -n "$f" ]; then last_ts=$(echo "$f" | awk '{print $1}')
			last=$(/bin/date -r "$last_ts" '+%Y-%m-%d' 2>/dev/null); fi
	fi
	recent=$([ "$last_ts" -gt 0 ] 2>/dev/null && [ $(( (now - last_ts) / 86400 )) -le 4 ] && echo yes || echo no)

	prune_candidate=unknown
	if [ "$prune_status" = available ]; then
		prune_candidate=$(jq -r --arg p "$wt" \
			'if any(.[]; .path == $p) then "candidate" else "-" end' "$prune")
	fi

	case "$dirty" in wip:*) bucket=hold-wip ;; *)
		case "$pr" in *OPEN*) bucket=hold-open-pr ;; *)
			if [ "$dirty" = unknown ] || [ "$merged" = unknown ] || [ "$remote" = unknown ] || [ "$pr" = unknown ]; then bucket=hold-unknown
			elif [ "$last_ts" -eq 0 ]; then bucket=review-no-history
			elif [ "$recent" = yes ]; then bucket=verify-recent-chat
			elif [ "$merged" = YES ]; then bucket=review-merged
			else bucket=review; fi ;;
		esac ;;
	esac

	printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
		"$size" "$age" "$merged" "$dirty" "$remote" "$pr" "$last" "$prune_candidate" "$herdr_state" "$marker" "$bucket" "$wt"
done | sort -t$'\t' -k1,1 -rh
