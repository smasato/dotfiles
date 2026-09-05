### Shipping

Land only the contiguous verified run that the user authorized. Read the gh-stack skill before stack operations and pstack-runtime before delegation or monitoring.

1. Identify the exact PRs, order, trunk, and authorized merge ceiling. A request to check or babysit is not merge authorization.
2. Have an independent worker verify each PR against its parent at the exact head SHA. Record the verdict and evidence. Use the actual surface for behavior changes. Post evidence externally only when authorized.
3. Stop the eligible run at the first PR without a passing verdict. Re-read current heads immediately before merging; a changed patch requires new verification.
4. For a native GitHub stack, follow the gh-stack skill's scoped merge procedure. Confirm whether the supplied target identifies a PR or the whole stack before execution, so the merge cannot exceed the ceiling. Use the repository's merge method and required remote flags. For an independent PR, use `gh pr merge` only for that PR.
5. Confirm the resulting GitHub state. A successful submission may mean queued, not merged. Watch the frozen PR list through `scripts/watch-pr/watch-pr` with the native monitoring mechanism until the eligible run completes or needs intervention.
6. While queued, leave topology, branch heads, and merge settings unchanged. Diagnose a stalled queue before any mutation. An ADVANCE result is progress; COMPLETE at the authorized ceiling is the terminal result.
7. Report merged PRs, queued or blocked PRs, verification evidence, and the next unverified item. Continuing beyond the ceiling requires a new authorized verification-and-merge pass.
