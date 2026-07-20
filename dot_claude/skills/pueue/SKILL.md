---
allowed-tools: Bash(pueue:*)
description: Run long-running commands (builds, downloads, batch jobs, full test suites — anything expected to take 2+ minutes) through the pueue task queue instead of run_in_background, so they survive session end and their logs are collected. Use before launching any command expected to run for minutes, or when Masato mentions pueue.
---

# Run Long Commands via pueue

The `pueued` daemon is already running (started by Homebrew services). Any command expected to take roughly 2 minutes or more goes through pueue, not `run_in_background` — pueue tasks survive the Claude Code session and keep their logs.

## Enqueue

- Bash(`pueue add --label "<short description>" -- <command>`)
  - The task runs in the current working directory; `cd` first or use `--working-directory <dir>` if the command must run elsewhere
  - The command runs in the daemon's environment, not this shell's — pass required environment variables explicitly, e.g. `pueue add -- env FOO=bar <command>`
  - Note the task id printed on success (`New task added (id <id>)`)

## Monitor

- Check state: Bash(`pueue status`)
  - Prefer polling with `pueue status` over blocking waits
- Read output: Bash(`pueue log <id>`), tail only with `--lines <n>`
- Live follow: Bash(`pueue follow <id>`) — only when actively watching; it blocks until the task ends
- Blocking wait: Bash(`pueue wait <id>`) — mind the Bash tool timeout; for anything long, poll `pueue status` instead

## On Failure

- Bash(`pueue log <id>`) shows the collected stdout/stderr — quote the decisive line when reporting
- Re-run a fixed or flaky task with Bash(`pueue restart <id>`)

## Cleanup

- Remove finished tasks once their results are no longer needed: Bash(`pueue clean`)
