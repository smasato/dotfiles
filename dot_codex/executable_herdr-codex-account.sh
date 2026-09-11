#!/bin/sh
# Report which ChatGPT account a Codex pane is logged into as herdr pane
# tokens so the agents sidebar can show it via $account / $seat in
# [ui.sidebar.agents.rows_by_agent]. Runs twice per pane: from the zsh `codex`
# wrapper right at launch (SessionStart only fires on the first prompt), and as
# the Codex SessionStart hook so resume / restore re-report (hooks.json is
# shared by every CODEX_HOME through symlinks, so one copy serves all seats).
#
#   account  plan name (Pro 20x / Pro 5x / Plus / Business; unknown shown raw)
#   seat     CODEX_HOME suffix (.codex_work1 -> w1); empty for the personal ~/.codex
set -eu

[ "${HERDR_ENV:-}" = "1" ] || exit 0
[ -n "${HERDR_PANE_ID:-}" ] || exit 0
command -v herdr >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

# Hook input arrives on stdin; the shell wrapper has a tty there, so skip it.
input=""
if [ ! -t 0 ]; then
  input=$(cat 2>/dev/null || true)
fi
# Mid-turn compaction re-fires SessionStart; the account cannot change there.
[ "$(printf '%s' "$input" | jq -r '.source // empty' 2>/dev/null)" != "compact" ] || exit 0

# Hooks are not documented to inherit CODEX_HOME, so fall back to the session
# transcript location (<home>/sessions/...) before assuming the default home.
codex_home="${CODEX_HOME:-}"
if [ -z "$codex_home" ]; then
  transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null)
  case "$transcript" in
    */sessions/*) codex_home="${transcript%%/sessions/*}" ;;
    *) codex_home="$HOME/.codex" ;;
  esac
fi
codex_home="${codex_home%/}"

auth="$codex_home/auth.json"
[ -r "$auth" ] || exit 0

# The plan lives in the id_token JWT claims (base64url payload).
payload=$(jq -r '.tokens.id_token // empty' "$auth" 2>/dev/null | cut -d. -f2 | tr '_-' '/+')
[ -n "$payload" ] || exit 0
case $(( ${#payload} % 4 )) in
  2) payload="${payload}==" ;;
  3) payload="${payload}=" ;;
esac
plan_type=$(printf '%s' "$payload" | base64 --decode 2>/dev/null \
  | jq -r '."https://api.openai.com/auth".chatgpt_plan_type // empty' 2>/dev/null) || exit 0

# Same names as ~/.local/bin/codex-usage, shortened to fit the sidebar.
case "$plan_type" in
  pro) account="Pro 20x" ;;
  prolite) account="Pro 5x" ;;
  plus) account="Plus" ;;
  self_serve_business_prolite) account="Business" ;;
  "") exit 0 ;;
  *) account="$plan_type" ;;
esac

case "$(basename "$codex_home")" in
  .codex_work*) seat="w${codex_home##*.codex_work}" ;;
  *) seat="" ;;
esac

# --seq makes re-reports overwrite older values when a pane is reused; herdr
# drops reports whose seq is not higher (compared across sources, so
# herdr-claude-account.sh uses the same unit), so use milliseconds (macOS date
# has no %N) with a seconds fallback.
# No --agent: the zsh wrapper reports before codex is running, and herdr drops
# an agent-labelled report when the pane has no live agent and last hosted a
# different one (a pane that just ran Claude would keep showing Team).
seq=$(perl -MTime::HiRes=time -e 'printf "%d", time * 1000' 2>/dev/null) || seq=$(date +%s)
herdr pane report-metadata "$HERDR_PANE_ID" \
  --source codex-account \
  --token "account=$account" --token "seat=$seat" \
  --seq "$seq" >/dev/null 2>&1 || true
exit 0
