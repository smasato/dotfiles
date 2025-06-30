# Create a Pull Request to GitHub

- Create a new branch
- Commit all changes
- Push the branch to GitHub
- Write PR description to `./PULL_REQUEST.md`
  - Check if a PR template (`PULL_REQUEST_TEMPLATE.md`) exists at the repository root or inside the `.github/` directory, and obtain its path if found.
  - Run Bash(find . -maxdepth 2 -type f -iname "PULL_REQUEST_TEMPLATE.md") to search for the template path:
  - If a template file is found, use its contents as the initial value for `./PULL_REQUEST.md`.
- Open `./PULL_REQUEST.md` in Cursor
  - I will review, modify and save the content
- Ask me if the PR description is correct
- Create a pull request using `./PULL_REQUEST.md` as the description
  - `gh pr create -t <title> --body-file ./PULL_REQUEST.md --assignee @me --base <base-branch>`
  - Usually create against the `main` branch. If the `main` branch doesn't exist, create against the `master` branch. If $ARGUMENTS is specified, use it as the base branch
- Execute `rm ./PULL_REQUEST.md`
- Execute `open <pull-request-url>`
