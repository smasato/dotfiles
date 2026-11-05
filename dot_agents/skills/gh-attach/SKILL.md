---
name: gh-attach
description: Attach local images or videos (screenshots, recordings) to a GitHub issue, PR, or comment with `gh --attach`. Use when posting or editing an issue/PR body or comment that should show a local image or video.
---

# Attach files to GitHub with `gh --attach`

`gh` uploads the file and writes its URL into the body, so it renders inline as if attached in the browser.

Supported commands: `gh issue create|edit|comment`, `gh pr create|edit|comment`.

## Steps

1. Confirm each file is an image or video. `gh` uploads only image and media types; for anything else (logs, zips), paste text into the body or ask the user.
2. Write the body to a Markdown file and reference each file at its local path where it should appear:
   - Image: `![what the screenshot shows](./shots/login.png)`; the alt text here is kept.
   - Video: `![](./rec/demo.mp4)` alone in its own paragraph renders as a player. Inside a sentence it renders as a link.
3. Run the command with `--body-file` and one `--attach` per file:

   ```shell
   gh pr comment 13 \
     --body-file ./body.md \
     --attach ./shots/login.png \
     --attach ./rec/demo.mp4
   ```

   `gh` rewrites each matching local reference to the uploaded URL. Attached files the body does not reference are appended to the end, in flag order.

4. Done when the command prints the issue/PR/comment URL. Open it (`gh pr view --web` or the printed URL) only if the user wants to check rendering.

Quick form with no body reference: `gh issue comment 42 --attach './login.png#Login error state'`. The text after `#` is the alt text; without it the filename is used.

## Rules

- Requires push access to the repository.
- Paths inside a `--body-file` resolve relative to that file's directory, then the working directory. Keep the body file next to the media or use paths relative to it.
- Repeat `--attach` for multiple files, up to 50 per command. The same file cannot be attached twice.
- Videos take no alt text: no `#alt` suffix.
- `#alt` in the flag applies only to appended files. A reference already in the body keeps its own alt text.
- Quote paths with spaces. Rename files whose path contains `#`: `#` starts the alt text, and quoting does not escape it.
- Rewriting works for every body source: `--body`, `--body-file`, stdin (`--body-file -`), and the editor.

Details: `gh pr comment --help`, https://docs.github.com/en/github-cli/github-cli/attaching-files-with-github-cli
