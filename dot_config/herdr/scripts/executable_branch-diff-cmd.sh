#!/bin/bash
# Print the hunk command for a whole-branch diff of the repo at $1: the current
# branch against the merge-base with its PR base branch (via gh, when an open
# PR exists) or the repo's default branch. Both hunk-diff.sh (prefix+shift+b /
# prefix+alt+b) and worktree-open.sh (tab 3 right pane) use this so the two
# stay in sync.
set -eu

dir="$1"

branch="$(git -C "$dir" branch --show-current 2>/dev/null || true)"
[ -n "$branch" ] || branch=HEAD

# PR base first: gh pr list matches open PRs whose head is this branch.
# Network call; on failure (offline, no auth, no PR) fall through silently.
base=""
if [ "$branch" != HEAD ] && command -v gh >/dev/null 2>&1; then
  pr_base="$(cd "$dir" && gh pr list --head "$branch" --limit 1 --json baseRefName --jq '.[0].baseRefName // empty' 2>/dev/null || true)"
  if [ -n "$pr_base" ] && git -C "$dir" rev-parse --verify --quiet "origin/$pr_base" >/dev/null 2>&1; then
    base="origin/$pr_base"
  fi
fi

# No PR: the repo's default branch (origin/HEAD first, then common candidates).
if [ -z "$base" ]; then
  base="$(git -C "$dir" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
fi
if [ -z "$base" ]; then
  for candidate in origin/main origin/master main master; do
    if git -C "$dir" rev-parse --verify --quiet "$candidate" >/dev/null 2>&1; then
      base="$candidate"
      break
    fi
  done
fi
[ -n "$base" ] || base=origin/main

# Diff from the merge-base so commits that landed on the base after the branch
# forked don't show up as reverse changes (same semantics as a PR diff).
range_start="$(git -C "$dir" merge-base "$base" "$branch" 2>/dev/null || true)"
[ -n "$range_start" ] || range_start="$base"

printf 'hunk diff %q..%q' "$range_start" "$branch"
