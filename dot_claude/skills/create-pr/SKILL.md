---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(find:*), Bash(gh pr create:*), Bash(rm ./PULL_REQUEST.md), Bash(open:*), Bash(hunk diff:*), Bash(herdr pane:*)
description: Create a pull request to GitHub. Use when the user asks to create a PR or open a pull request.
---

# Create a Pull Request to GitHub

Status: !`git status`
Diff: !`git diff`
Base branch: !`git branch | grep -E "master|main"` or $ARGUMENTS

- Create a new branch
  - Read @README.md to check the branch naming convention
- Commit all changes
- Push the branch to GitHub
- Write PR description to `./PULL_REQUEST.md`
  - Do not write the PR title in `./PULL_REQUEST.md`; the file is used verbatim as the PR body
  - Run Bash(`find . -maxdepth 2 -type f -iname "PULL_REQUEST_TEMPLATE.md"`) to search for `<template-path>`
  - Read(`<template-path>`) to get the template content
  - If a template file is found, use its contents as the initial value for `./PULL_REQUEST.md`
- Show `./PULL_REQUEST.md` with hunk so I can review it
  - `PULL_REQUEST.md` is git-ignored, so a working-tree diff cannot show it; compare it against an empty file instead
    - Bash(`: > "${TMPDIR:-/tmp}/empty.md"`)
    - The hunk command is: `hunk diff "${TMPDIR:-/tmp}/empty.md" ./PULL_REQUEST.md`
  - If running inside Herdr (`$HERDR_ENV` is `1`), open it in a pane:
    - Bash(`herdr pane split --current --direction right --no-focus`) and read `pane_id` from the JSON response
    - Bash(`herdr pane run <pane-id> "<the hunk command>"`)
    - hunk does not reload file comparisons; whenever `./PULL_REQUEST.md` changes, refresh with Bash(`herdr pane send-keys <pane-id> q`) and rerun the hunk command via `herdr pane run`
  - Otherwise, tell me to run the hunk command in my terminal
- I will review, modify and save the content
- Ask me if the PR description is correct (y/n)
- If I say "y", Create a pull request using `./PULL_REQUEST.md` as the description
  - Make the title from the branch's commit messages, following the semantic commit format
  - Bash(`gh pr create -t <title> --body-file ./PULL_REQUEST.md --assignee @me --base <Base branch>`)
- Bash(`rm ./PULL_REQUEST.md`)
- If a hunk pane was opened, Bash(`herdr pane close <pane-id>`)
