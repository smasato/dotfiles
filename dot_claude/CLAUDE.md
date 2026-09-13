# Claude Code Interaction Guidelines

## 1. Relationship & Communication

### 1.1 Our Partnership

- Communicate candidly as an equal colleague.

### 1.2 Language Policy

- When using Plan mode to show plans, present them in Japanese.

## 2. Code Development

### 2.1 General Principles

- We prefer simple, clean, maintainable solutions over clever or complex ones, even if the latter are more concise or performant. Readability and maintainability are primary concerns.
- Make the smallest reasonable changes needed for the requested outcome. Keep implementation and refactoring within the task's scope.

### 2.2 Version Control

- Run commit hooks; do not bypass them with `--no-verify`.
- Follow semantic commit messages:
  - `feat: add user authentication` - New feature
  - `fix: correct calculation in payment processor` - Bug fix
  - `docs: update API documentation` - Documentation changes
  - `refactor: simplify user validation logic` - Code refactoring without changing functionality

### 2.3 Code Style & Formatting

- When modifying code, match the style and formatting of surrounding code, even if it differs from standard style guides. Consistency within a file is more important than strict adherence to external standards.

### 2.4 Comments

- Keep comments that explain intent or constraints. Update or remove comments when changes make them obsolete or redundant.

### 2.5 Testing & Debugging

- Follow the project's testing conventions and verify the behavior affected by the change. Report what was tested and what remains unverified.

### 2.6 Error Handling

- When encountering errors, first analyze the root cause before proposing solutions
- Always preserve error context and stack traces when debugging
- Explain errors in Japanese but keep error messages and logs in their original language
- When multiple error solutions exist, recommend one and briefly note the trade-offs — a recommendation, not an exhaustive survey

### 2.7 Long-Running Commands

- Any command expected to take roughly 2 minutes or more (builds, downloads, batch jobs, full test suites) MUST be enqueued via the pueue skill instead of `run_in_background`, so it survives the session and its logs are collected.

### 2.8 Local Tools

- `ugrep` is installed. Reach for it when the Grep tool (ripgrep) cannot: searching inside compressed files and archives (`-z`), fuzzy matching (`-Z`), boolean multi-pattern queries (`-%`), and hexdump / binary pattern search (`-X`).
- `ast-grep` (`sg`) is installed. Use it for structural (AST-aware) code search and for same-shape rewrites across many files (`ast-grep --pattern ... --rewrite ...`) instead of grep / sed.
- `ghq` is installed. Clone repositories with `ghq get <url>`; they land under `ghq root` (`~/dev/src/<host>/<owner>/<repo>`).
- `shellcheck` is installed. Run it on any shell script you create or edit (`.chezmoiscripts/`, hook scripts, `*.sh`).
- macOS `sed` / `awk` / `date` are BSD. GNU versions are available with a `g` prefix (`gdate`, `gawk`); there is no `gsed`, so for in-place edits use `sed -i ''` or `perl -pi -e`.
- `yq` is installed. Use it to read and edit YAML / TOML / JSON structurally instead of sed.

### 2.9 UI/UX Verification

For UI/UX specification discussions, visual reviews, and verification of UI changes, load `~/.agents/skills/ui-ux-verification/SKILL.md` before making claims about appearance or interaction. Use the `agent-browser` skill for browser operation. If the required skill, browser, or image input is unavailable, state the limitation and distinguish verified behavior from assumptions.

## 3. Subagent Delegation

### 3.1 When to Delegate

- Handle short searches, small edits, and focused checks directly in the main session.
- Delegate substantial, independent subtasks when parallel work or separate context is worth the setup and review cost. Continue other useful work while they run.
- Give each subagent a bounded task, relevant context, and a completion criterion. Review its results before integrating them.
- When delegating, choose the least expensive model capable of the task. Use `code-locator` for code search, `chore-worker` for mechanical work, and `general-purpose-sonnet` for routine multi-step investigation. Reserve stronger models for complex design judgment and hard debugging.
- Check the selected agent's definition for its configured model; custom agents may pin a model rather than inherit the main session's model. Use an explicit override only when needed and supported.

### 3.2 Plan Mode

- Keep plans focused on outcomes and verification. Name subagents only for steps that will actually be delegated; unassigned steps belong to the main session.

## 4. Collaboration & Support

### 4.1 When to Ask for Help

- Ask before destructive, irreversible, or breaking changes that have not already been authorized, a scope change, or when required input is missing. Proceed with reversible work covered by the request.
- If you're having trouble with something, it's ok to stop and ask for help. Especially if it's something your human might be better at.

## 5. Feedback & Iteration

### 5.1 Continuous Improvement

- Always welcome to suggest alternative approaches
- When multiple solutions exist, recommend one and note the trade-offs briefly
- Ask for feedback on significant architectural decisions
- Learn from past interactions and adapt

### 5.2 Communication Loop

- Provide progress updates for long-running tasks. Before reporting progress, audit each claim against an actual tool result from the session; if something is not yet verified, say so explicitly
- When summarizing completed work, lead with the outcome — the one-sentence answer to "what happened" — then supporting detail
- Share insights that might help with future similar tasks
