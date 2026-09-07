### Refactoring

Change structure while preserving the agreed behavior. Keep newly discovered bugs and features outside the refactor unless the user approves them.

1. Name the behavior to preserve and run the existing checks that exercise it before editing. Reuse tests, snapshots, or reproduction commands. Add focused characterization coverage only where existing checks cannot prove the relevant contract. For mechanical changes, use compiler checks and reference searches where they establish the required property; they do not prove runtime equivalence.
2. State the target structure and what it simplifies. Read the affected code directly; use `how` if the contract is unclear. Use `architect` only for unresolved design alternatives or consequential interface changes, not merely because the edit crosses a function boundary.
3. Make small behavior-preserving changes. Keep cleanup within the named scope. Search callers, strings, docs, and back-references when renaming or moving APIs. Migrate owned callers together where safe; preserve compatibility when external consumers or deployment order require it.
4. Work inline for local edits. Delegate separable mechanical work when it saves effort, with explicit file ownership and isolated writes. Coordinate shared Git operations and review the resulting diff.
5. Re-run the baseline checks. Add an equivalence comparison or an interactive smoke test when the changed behavior requires it. Report the actual commands and results, including gaps; a delegate's summary alone is not proof.
6. Confirm that the diff improves the intended structure without changing behavior. Stop after verification unless commits or publication are authorized. Follow repository commit conventions and use **Opening a PR** only for an authorized PR.

**Reply:** structural change, preserved contract, verification evidence, and any remaining risk. No new behavior.
