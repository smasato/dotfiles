"""Read plugin state from each installed CLI, including existing work homes."""
import json
import os
from pathlib import Path
import subprocess
import sys


def inspect(kind, home):
    env = dict(os.environ)
    env.pop("CLAUDE_CONFIG_DIR", None)
    env.pop("CODEX_HOME", None)
    if kind == "codex":
        env["CODEX_HOME"] = str(home)
        command = ["codex", "plugin", "list", "--marketplace", "worktrunk", "--json"]
    else:
        if home.name != ".claude":
            env["CLAUDE_CONFIG_DIR"] = str(home)
        command = ["claude", "plugin", "list", "--json"]
    data = json.loads(subprocess.check_output(command, env=env, text=True, timeout=60))
    if kind == "codex":
        return any(p.get("pluginId") == "worktrunk@worktrunk" and p.get("installed") is True
                   and p.get("enabled") is True for p in data["installed"])
    return any(p.get("id") == "worktrunk@worktrunk" and p.get("scope") == "user"
               and p.get("enabled") is True for p in data)


def main():
    failed = False
    for kind, names in (("claude", (".claude", ".claude_work")),
                        ("codex", (".codex", ".codex_work1", ".codex_work2", ".codex_work3"))):
        for name in names:
            home = Path.home() / name
            if not home.exists():
                print(f"{name}: absent (not checked)")
                continue
            try:
                enabled = inspect(kind, home)
                print(f"{name}: {'installed and enabled' if enabled else 'missing or disabled'}")
                failed |= not enabled
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
                print(f"{name}: unable to verify: {error}", file=sys.stderr)
                failed = True
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
