#!/bin/sh
# Report the Claude account type (Team/Max) as a herdr pane token so the
# agents sidebar can show which account each Claude pane is logged into
# via the $account token in [ui.sidebar.agents.rows_by_agent].
set -eu

[ "${HERDR_ENV:-}" = "1" ] || exit 0
[ -n "${HERDR_PANE_ID:-}" ] || exit 0
command -v herdr >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

# .claude.json lives in $CLAUDE_CONFIG_DIR when set (e.g. pclaude), else $HOME.
cfg="${CLAUDE_CONFIG_DIR:-$HOME}/.claude.json"
[ -r "$cfg" ] || exit 0

org_type=$(jq -r '.oauthAccount.organizationType // empty' "$cfg" 2>/dev/null) || exit 0

case "$org_type" in
  claude_team) label="Team" ;;
  claude_max) label="Max" ;;
  "") exit 0 ;;
  *) label="$org_type" ;;
esac

# --seq makes re-reports overwrite older values when a pane is reused.
herdr pane report-metadata "$HERDR_PANE_ID" \
  --source claude-account --agent claude \
  --token "account=$label" --seq "$(date +%s)" >/dev/null 2>&1 || true
exit 0
