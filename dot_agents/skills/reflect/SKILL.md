---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

Read [pstack runtime](../pstack-runtime/SKILL.md) before executing this workflow. It defines native delegation, model roles, history, and monitoring for Claude Code and Codex.

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

- The user said "reflect" or "/reflect".
- A complex task (5+ tool calls) just landed cleanly and the recipe is worth keeping.
- The agent hit dead ends, found the working path, and the path generalizes.
- The user corrected the agent's approach mid-task.
- A non-trivial workflow emerged that isn't captured anywhere.

Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

Locate the active session using pstack-runtime's scoped history reference. Match session metadata and the task before reading its body. If a transcript is unavailable, pass a digest and mark claims requiring tool-event evidence as unverified.

### 2. Spawn three reviewers in parallel

Use the native runtime to launch three reviewers, with distinct lenses below and read-only briefs. Include any connected MCP tools needed for citations. The parent applies approved edits.

| Lens      | Model role to resolve  | Prompt template                    |
| --------- | ---------------------- | ---------------------------------- |
| Judgment  | native `judgment` role | `references/judgment-reviewer.md`  |
| Tooling   | native `code` role     | `references/tooling-reviewer.md`   |
| Divergent | native `judgment` role | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the delegation response body.

### 3. Synthesize

Use a fresh judgment-role worker to synthesize. Give it a read-only brief and `references/synthesizer.md` with the reviewer outputs. It returns Accepted / Rejected / Backlog.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. The synthesizer already applies this criterion; this is a final pass before edits land. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org; do not auto-apply.

Include backlog items in the report. Submit them to an external tracker only when the user's request authorizes that.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to the installed `skill-creator` skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `skill-creator` and run its description-optimization loop.
- `new skill via skill-creator: <kebab-name>`: hand creation to `skill-creator`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
