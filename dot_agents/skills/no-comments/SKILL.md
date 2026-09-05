---
name: no-comments
description: 'Spawn Comment Sicko, fix accepted findings, and offer encodings for claimed constraints.'
disable-model-invocation: true
---

Read [pstack runtime](../pstack-runtime/SKILL.md) before executing this workflow. It defines native delegation, model roles, history, and monitoring for Claude Code and Codex.

# No comments

Spawn Comment Sicko. Act on accepted findings.

Authoring agents defend comments. Defer to Comment Sicko's fresh perspective.

## Scope

Use the caller's files or diff. Otherwise use the current diff against the base branch, default `main`, including the working tree.

## Steps

1. Read `references/comment-sicko.md` in full. Spawn the comment reviewer through pstack-runtime, passing the scope and whether edits are authorized. Claude uses `comment-sicko`; Codex gets the full prompt in a fresh worker. With delegation unavailable, perform the same review locally and disclose the lack of an independent reviewer.
2. Inspect its report and diff. Reject application-code edits, scope escapes, exception-protected deletions, misstated `MUST KILL` reasons, and flags that treat kept intentional code as guilty. Audit missed scoped lint and TypeScript suppressions; verify their effect before accepting removal. Before accepting thin `IMPORTANT` or `do not remove` kills or keeps, run `/how` or `/why` on their symbol. Preserve or restore ambiguous comments and report the uncertainty for the parent to decide. Revert and rerun one rejected report with the failure named. Reject a second, report it open, and fail `/no-comments`.
3. Fix trivial accepted flags directly by deleting a dead path, dropping a parameter, or using the real API. If any fix needs a shape, run `/architect` once for the accepted set and surrounding code. Stop at the sketch. Architect shapes. Step 4 implements.
4. Implement the smallest root-cause fix in scope. Remove every named workaround. If the root cause is out of scope, land the smallest in-scope fix and report the rest open. The **principle-fix-root-causes** and **principle-redesign-from-first-principles** skills guide intent only: fix real causes, redesign as if requirements always existed, never bolt on symptom guards. Neither authorizes widening the fence nor fixing instances outside it.
5. Constraint comments say `do not remove`, `do not change wording`, or `talk to X before changing`. Leave keeps about things we cannot change. Offer the cheapest in-scope type, runtime, test, or CI lint. Wait for interactive approval. Unattended and eval require caller pre-approval. If approved, encode then delete. Otherwise preserve the comment, report the constraint open, and sketch out-of-scope work.
6. Report the deletion count, restored comments, reruns, architect sketch, fixes, encoding offers, encodings, unenforced constraints, and other open work.
