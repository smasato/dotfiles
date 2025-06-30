---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(find:*), Bash(gh pr create:*), Bash(rm ./PULL_REQUEST.md), Bash(open:*)
description: Create a pull request to GitHub
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
  - Check if a PR template (`PULL_REQUEST_TEMPLATE.md`) exists at the repository root or inside the `.github/` directory, and obtain its path if found.
  - Run Bash(`find . -maxdepth 2 -type f -iname "PULL_REQUEST_TEMPLATE.md"`) to search for the template path:
  - If a template file is found, use its contents as the initial value for `./PULL_REQUEST.md`.
- Bash(`cursor ./PULL_REQUEST.md`)
  - I will review, modify and save the content
- Ask me if the PR description is correct (y/n)
- If I say "y", Create a pull request using `./PULL_REQUEST.md` as the description
  - Read(`./PULL_REQUEST.md`) to make the title
  - Bash(`gh pr create -t <title> --body-file ./PULL_REQUEST.md --assignee @me --base <Base branch>`)
- Bash(`rm ./PULL_REQUEST.md`)
- Bash(`open <pull-request-url>`)
