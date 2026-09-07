### Bug fix

Own the diagnosis, the fix, and its verification. Use the repository's debugging and test workflows first.

1. Establish a failing case before editing. Prefer an existing focused test or reproduction command. Use a control skill when the bug needs an interactive runtime. If access or reproducibility blocks proof, state what you tried and what remains unverified; ask only for the missing input or access.
2. Test hypotheses against the failing case until the cause is supported by evidence. Read the affected code directly. Use `how` for unclear runtime flow and `why` when regression history could resolve a specific question. Add temporary instrumentation only when needed.
3. Make the smallest fix that addresses the cause. Crossing a function boundary does not require a design review. Use `architect` only when competing designs or a consequential interface change need comparison. Work inline for a local fix; delegate independent investigations or a bounded implementation when the handoff helps. Give each writer an isolated scope and review its diff.
4. Re-run the original failing case and relevant surrounding checks. Add a regression test through the existing test setup when practical. Keep failing-then-passing evidence; an inconclusive run is not a pass. Remove experimental changes that the evidence did not justify, without disturbing unrelated work.
5. Stop at the requested stage. A diagnosis request ends before edits. Commit only when authorized, following repository conventions; separate failing-test commits are optional. Use **Opening a PR** only when publication is authorized.

**Reply:** cause, change, failing-then-passing evidence, and any verification limits. Quote the relevant output rather than dumping whole logs.
