# Skill authoring

Use the installed `writing-for-agents` skill and its skill-mechanics reference for authoring. If `skill-creator` is installed, use it when a structured evaluation or description-tuning loop would help. Neither helper is required, and a missing helper does not authorize installing it.

Without a helper, follow the repository's existing skill layout and these rules:

- Edit an existing skill when it already owns the workflow. Create a new one only for a distinct, recurring trigger.
- Put the skill in `<skill-name>/SKILL.md` with YAML frontmatter containing `name` and a single scalar `description`. Quote punctuation or use an indented block scalar as needed.
- Preserve invocation policy on edits. For new skills, decide whether autonomous invocation is intended. Explicit-only skills use `disable-model-invocation: true` and, for Codex, `agents/openai.yaml` with nested `policy.allow_implicit_invocation: false`. Keep both policies consistent.
- State triggers, authorized actions, ordered steps, and a checkable stopping condition. Move branch-specific detail into linked reference files.
- Use general rules rather than private transcript excerpts, session IDs, internal URLs, or work-specific examples.

Validate touched files with the repository's available formatters, skill validators, and link checks. Confirm that each validator covers the touched skill; a manifest-only check may not cover a newly created one. If no validator covers it, inspect frontmatter, paths, links, and invocation metadata directly and report that limitation.

For changed behavior or triggers, check representative matching and non-matching scenarios. Distinguish a manual walkthrough from an actual agent evaluation. Run a larger benchmark only when requested or when observed trigger failures justify it. Stop at the authorized draft, edit, or publication stage.
