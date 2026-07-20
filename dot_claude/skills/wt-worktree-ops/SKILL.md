---
name: wt-worktree-ops
description: Perform ALL git worktree operations (create, switch, list, merge, remove, cleanup) through the wt (worktrunk) CLI instead of raw `git worktree` / `git branch -d` commands. Use this skill whenever the user asks to create, remove, merge, or clean up a worktree, mentions ワークツリー or worktree, or when cleaning up worktrees left behind by subagents (Agent tool worktree isolation, directories like `<repo>.agent-*`). Also use it before running any `git worktree ...` command yourself — that command should almost always be replaced by a wt equivalent.
---

# Worktree operations via wt (worktrunk)

This machine manages worktrees with worktrunk (`wt`). Raw `git worktree` /
`git branch -d` bypass wt's hooks (post-start, post-merge, etc.), its branch
cleanup logic, and its worktree layout — leaving inconsistent state. Always
prefer the wt equivalent.

## Command mapping

| Task | Use | Not |
| --- | --- | --- |
| Create worktree + branch | `wt switch --create <branch>` | `git worktree add` |
| Switch to existing worktree | `wt switch <branch>` | `cd` by hand |
| List worktrees | `wt list` | `git worktree list` |
| Merge branch into default branch and clean up | `wt merge` (run inside the worktree) | `git merge` + `git worktree remove` + `git branch -d` |
| Remove worktree (branch deleted if merged) | `wt remove [branch-or-path]` | `git worktree remove` + `git branch -d` |

## Merge behavior — check before running

`wt merge` by default: squashes commits, rebases onto the target,
fast-forwards the target branch, removes the worktree, and runs hooks.
Flags to deviate:

- Keep individual commits: `--no-squash`
- Keep the worktree afterwards: `--no-remove`
- Merge commit instead of fast-forward: `--no-ff`

Squash-by-default changes history shape — if the branch has multiple
meaningful commits, confirm with the user (or pass `--no-squash`) rather
than silently squashing.

## Cleaning up subagent worktrees

The Agent tool's worktree isolation creates worktrees outside wt (sibling
directories like `/path/to/repo.agent-<id>` on branches named `agent-<id>`).
Clean these up with wt too — `wt remove <branch-or-path>` works on any git
worktree of the repo and deletes the branch only if merged:

```sh
wt remove agent-a1448e26462a6531d          # by branch name
wt remove /path/to/repo.agent-a1448e26...  # or by path
```

Unmerged branch that should still be deleted: `wt remove -D <branch>`.
Dirty worktree: removal fails without `-f` — inspect the changes before
forcing; they may be work the user wants.

## When raw git worktree is acceptable

Only when wt itself cannot do the job (e.g. `wt` is not installed in the
environment, or repairing state wt refuses to touch). Say so explicitly
when falling back.
