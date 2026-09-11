#!/bin/sh
# Report which ChatGPT account a Codex pane is logged into, how it was launched
# and how much quota is left, as herdr pane metadata. Runs from the zsh `codex`
# wrapper right at launch (SessionStart only fires on the first prompt) and as
# the Codex SessionStart / Stop hooks so resume / restore and every finished
# turn re-report (hooks.json is shared by every CODEX_HOME through symlinks, so
# one copy serves all seats).
#
#   $account       plan name (Pro 20x / Pro 5x / Plus / Business; unknown shown raw)
#   $launch        command that started this pane: codex, or wcodexN from the
#                  CODEX_HOME suffix (.codex_work1 -> wcodex1)
#   display_agent  "<launch> · <usage>" shown in the pane border in place of
#                  "codex"; usage is codex-usage --compact (S/W used% and reset
#                  time). Fetched in the background so hooks return at once.
#
#   herdr-codex-account.sh clear   drop display_agent / $launch after codex
#                                  exits so a reused pane does not keep them
set -eu

[ "${HERDR_ENV:-}" = "1" ] || exit 0
[ -n "${HERDR_PANE_ID:-}" ] || exit 0
command -v herdr >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

# --seq makes re-reports overwrite older values when a pane is reused; herdr
# drops reports whose seq is not higher (compared across sources, so
# herdr-claude-account.sh uses the same unit), so use milliseconds (macOS date
# has no %N) with a seconds fallback.
# No --agent: the zsh wrapper reports before codex is running, and herdr drops
# an agent-labelled report when the pane has no live agent and last hosted a
# different one (a pane that just ran Claude would keep showing Team).
now_seq() {
  perl -MTime::HiRes=time -e 'printf "%d", time * 1000' 2>/dev/null || date +%s
}

if [ "${1:-}" = "clear" ]; then
  herdr pane report-metadata "$HERDR_PANE_ID" \
    --source codex-account \
    --clear-display-agent --clear-token launch \
    --seq "$(now_seq)" >/dev/null 2>&1 || true
  exit 0
fi

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
  .codex_work*) launch="wcodex${codex_home##*.codex_work}" ;;
  *) launch="codex" ;;
esac

herdr pane report-metadata "$HERDR_PANE_ID" \
  --source codex-account \
  --token "account=$account" --token "launch=$launch" \
  --display-agent "$launch" \
  --seq "$(now_seq)" >/dev/null 2>&1 || true

# The usage fetch is a network call (up to 20s), so run it detached: the hook
# and the shell wrapper return immediately and the border updates when it lands.
usage_cmd="$HOME/.local/bin/codex-usage"
[ -x "$usage_cmd" ] || exit 0
(
  usage=$("$usage_cmd" --codex-home "$codex_home" --compact 2>/dev/null) || exit 0
  [ -n "$usage" ] || exit 0
  herdr pane report-metadata "$HERDR_PANE_ID" \
    --source codex-account \
    --display-agent "$launch · $usage" \
    --seq "$(now_seq)" >/dev/null 2>&1 || true
) </dev/null >/dev/null 2>&1 &
exit 0
