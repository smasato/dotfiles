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

| Task                                          | Use                                  | Not                                                   |
| --------------------------------------------- | ------------------------------------ | ----------------------------------------------------- |
| Create worktree + branch                      | `wt switch --create <branch>`        | `git worktree add`                                    |
| Switch to existing worktree                   | `wt switch <branch>`                 | `cd` by hand                                          |
| List worktrees                                | `wt list`                            | `git worktree list`                                   |
| Merge branch into default branch and clean up | `wt merge` (run inside the worktree) | `git merge` + `git worktree remove` + `git branch -d` |
| Remove worktree (branch deleted if merged)    | `wt remove [branch-or-path]`         | `git worktree remove` + `git branch -d`               |

## Inspecting worktrees

| Task                                   | Command                                      |
| -------------------------------------- | -------------------------------------------- |
| Check every worktree's working changes | `wt step for-each -- git status --short`     |
| Resolve the primary worktree path      | `wt step eval '{{ primary_worktree_path }}'` |
| Preview integrated cleanup candidates  | `wt step prune --dry-run --min-age=2d`       |

`for-each` executes argv directly and sequentially. Use `sh -c` explicitly for
pipes or redirects. Command failures are collected and execution continues;
template expansion errors stop the run. For detached worktrees, use
`{{ branch | default(short_commit) }}` when a label is needed.

The prune preview supplements usage checks; it does not establish that a chat
has finished or that ignored files are disposable. Keep checking active chats,
PRs, and uncommitted files, then use `wt remove <path>` for confirmed targets.
The JSON preview is an array with `path` and a predicted `branch_deleted`,
not the `wt list` envelope. Branch-only candidates have a null path.

## Existing remote branches

To open an existing remote branch, use `wt switch origin/<branch>`; fetch that
remote first if its tracking ref is missing. Herdr's picker accepts the same
remote-qualified name. Reserve `--create` for a new branch: it starts at `--base`
or the default branch even when a same-named remote branch exists.

With v0.76+, `wt switch --create foo --base origin/foo` tracks `origin/foo`,
while `--create bar --base origin/foo` has no upstream. The global sync hook
has been removed, so a same-named remote does not override an explicit base.

New worktrees copy local settings from the primary worktree only when its
`.worktreeinclude` exists. Files must be both ignored and included; existing
destinations are preserved. Existing worktrees do not recopy on switch.
If copying fails, fix the cause and run `wt step copy-ignored --require-include`
in the new worktree before resuming startup. The checkout and partial copies remain.

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
