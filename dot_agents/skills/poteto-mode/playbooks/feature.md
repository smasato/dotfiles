### Feature

Follow the [execution contract](../../pstack-runtime/SKILL.md). Use the project's existing feature workflow when it supplies the necessary steps and checks.

1. Establish observable acceptance conditions, non-goals, and authorized delivery stage. Trace the relevant entry points and existing data model; use `how` when the surrounding behavior is unclear.
2. Choose the responsible boundary and reuse fitting patterns. Compare alternatives with `architect`, `arena`, or a prototype only when the design is consequential and unsettled.
3. Identify independent slices and shared state. Delegate useful independent work under the [delegation contract](../../pstack-runtime/references/delegation.md); keep tightly coupled code with one owner. Include test data, dev servers, hooks, and repository operations in the ownership plan.
4. Implement in verifiable units. Preserve unrelated changes and inspect shared consumers affected by the requested change. Small local work can stay in the main session.
5. Verify the affected behavior using the project's tests and, where relevant, its UI or CLI verification workflow. Compare relevant states and related views rather than checking initial rendering alone. Report unavailable evidence instead of calling it a pass.
6. Review the diff and stop at the authorized stage. If commits or PRs are requested, choose boundaries that help review; multiple commits can belong in one PR. Follow [PR creation](opening-a-pr.md) only when authorized.

**Reply:** outcome, consequential choices, verification, and unresolved decisions. Do not list unused workflows or manufacture design alternatives for the report.
