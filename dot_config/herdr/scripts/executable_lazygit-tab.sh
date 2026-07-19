#!/bin/bash
# Open (or switch/toggle) the herdr-lazygit tab via the plugin action, then
# pin the tab label to "lazygit" — herdr labels tabs with bare numbers and the
# plugin offers no way to name the tab it creates.
set -eu

herdr plugin action invoke open-tab --plugin herdr-lazygit

# The pane opens asynchronously; poll briefly for "Git" panes that are the
# only pane in their tab (the tab variant — split lazygit panes share a tab
# with other panes). On the toggle-close path nothing matches and we time out.
for _ in 1 2 3 4 5 6 7 8 9 10; do
  tab_ids="$(herdr pane list 2>/dev/null | python3 -c '
import json, sys
from collections import Counter
try:
    panes = json.load(sys.stdin)["result"]["panes"]
except Exception:
    sys.exit(0)
panes = [p for p in panes if isinstance(p, dict)]
counts = Counter(p.get("tab_id") for p in panes)
for p in panes:
    if p.get("label") == "Git" and counts[p.get("tab_id")] == 1:
        print(p.get("tab_id"))
')"
  if [ -n "${tab_ids}" ]; then
    for tab_id in ${tab_ids}; do
      herdr tab rename "${tab_id}" lazygit >/dev/null 2>&1 || true
    done
    exit 0
  fi
  sleep 0.2
done
