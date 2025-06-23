# Create a Pull Request to GitHub

- Create a new branch
- Commit all changes
- Push the branch to GitHub
- Write PR description to `./tmp/PULL_REQUEST.md`
  - If `./PULL_REQUEST_TEMPLATE.md` exists, use it as the template for the PR description
- Open `./tmp/PULL_REQUEST.md` in Cursor
  - I will review, modify and save the content
- Ask me if the PR description is correct
- Create a pull request using `./tmp/PULL_REQUEST.md` as the description
  - `gh pr create -t <title> --body-file ./tmp/PULL_REQUEST.md --assignee @me --base <base-branch>`
  - Usually create against the `main` branch. If the `main` branch doesn't exist, create against the `master` branch. If $ARGUMENTS is specified, use it as the base branch
- Execute `rm ./tmp/PULL_REQUEST.md`
- Execute `open <pull-request-url>`
