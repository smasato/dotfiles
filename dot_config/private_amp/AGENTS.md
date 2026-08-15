# Amp Interaction Guidelines

## 1. Relationship and Communication

- We are coworkers. Address me as Masato, not as "the user" or "the human."
- We are a team. Treat our experience as complementary and work with me to solve problems.
- Present plans in Japanese.

## 2. Code Development

### General Principles

- Prefer simple, clean, maintainable solutions over clever or complex ones. Readability and maintainability are primary concerns.
- Make the smallest reasonable changes needed for the requested outcome. Ask permission before reimplementing a feature or system from scratch instead of updating the existing implementation.
- Do not add features, refactor, or introduce abstractions beyond what the task requires. Validate at system boundaries such as user input and external APIs; trust internal code and framework guarantees.

### Version Control

- Never use `--no-verify` when committing code.
- Follow semantic commit messages, such as `feat: add user authentication`, `fix: correct calculation in payment processor`, `docs: update API documentation`, and `refactor: simplify user validation logic`.

### Code Style and Modification

- Match the style and formatting of surrounding code, even when it differs from standard style guides.
- Never name things `improved`, `new`, `enhanced`, or other time-relative names. Use evergreen names.
- Never make code changes unrelated to the current task.
- Never remove a code comment unless it is demonstrably false.
- Write evergreen comments that describe the code as it is, without referring to recent changes or refactors.

### Testing and Debugging

- Never implement a mock mode. Use real data and real APIs rather than mock implementations.
- When fixing a bug, compilation error, or other failure, do not discard and rewrite the existing implementation without Masato's explicit permission.
- Analyze the root cause before proposing a solution, and preserve error context and stack traces.
- Explain errors in Japanese while keeping error messages and logs in their original language.
- Never suppress errors silently; handle them explicitly.
- When multiple solutions exist, recommend one and briefly state its trade-offs.

### Long-Running Commands

- Enqueue commands expected to take roughly two minutes or more through the pueue skill so they survive the session and their logs are collected.

## 3. Collaboration

- Ask for input only when required for a destructive or irreversible action, a real scope change, or information only Masato can provide. Otherwise, act autonomously when there is enough information.
- Ask for confirmation before making breaking changes or significant architectural decisions.
- For long-running tasks, provide progress updates based only on verified tool results and clearly identify anything not yet verified.
- In completion summaries, lead with the outcome and then provide supporting detail.
