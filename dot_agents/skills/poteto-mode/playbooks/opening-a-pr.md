### Opening a PR

Use only when PR creation or publication is authorized. Reaching the end of another playbook does not grant permission. Follow the [execution contract](../../pstack-runtime/SKILL.md) and the repository's PR template and delivery skills.

1. Inspect the current worktree, diff, base, and head. Preserve unrelated changes. Use the installed `wt-worktree-ops` workflow if an isolated worktree is needed; keep repository-wide operations with its owner.
2. Run the relevant local checks and review the final diff. Preserve useful comments and legal or required directives. A separate comment audit or design panel is not a routine PR prerequisite.
3. Create reviewable commits when authorized, following the repository's commit convention and hooks. Do not rewrite history merely to make every commit a separate PR. One coherent PR can contain multiple commits.
4. Write the description from the actual diff and verification evidence. Prefer the repository template; otherwise state intent, scope, material trade-offs, and checks performed. Exclude private history and unrelated task details from public artifacts.
5. For an existing PR, fetch the current body and preserve managed or bot-owned sections. Update the description before pushing new changes so reviewers see the matching scope.
6. For stacks, use the installed `gh-stack` workflow and the actual trunk. Only the stack owner changes topology. Recheck heads and affected evidence after base or branch changes.
7. Publish with the requested draft or ready status. Confirm the resulting PR state before reporting its URL. Monitoring, auto-merge, merging, and worktree cleanup require their own authorization unless already included in the request.

Use concise, concrete titles. Apply the project's writing checks without restating them here. Attach screenshots or other artifacts only when they support the change and are appropriate for the repository's visibility.

**Reply:** PR URL, scope, verification, and any remaining blocker. Stop unless further work was authorized.
