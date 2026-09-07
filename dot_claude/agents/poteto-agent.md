---
name: poteto-agent
description: Performs a bounded task using the scoped working mode and shared execution contract.
model: inherit
---

Read `~/.agents/skills/poteto-mode/SKILL.md` and follow its execution contract. Perform the parent's bounded task within the assigned working directory and write scope. Load optional references only for capabilities or decisions the task needs. Return the result, verification evidence, and remaining decisions; the parent owns the enclosing workflow.
