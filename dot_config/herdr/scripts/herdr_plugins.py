"""Install configured Herdr plugins, refresh their skills, and record revisions."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
from herdr_common import call, save

PLUGINS = {
    "worktrunk": "devashish2203/herdr-worktrunk",
    "herdr-file-viewer": "smarzban/herdr-file-viewer",
    "herdr-lazygit": "crokily/herdr-lazygit",
}


def inventory():
    plugins = call("plugin", "list", "--json")["plugins"]
    if not isinstance(plugins, list):
        raise ValueError("Invalid Herdr plugin inventory")
    return {plugin["plugin_id"]: plugin for plugin in plugins if plugin["plugin_id"] in PLUGINS}


def revisions(plugins):
    return {name: dict(version=plugin["version"], commit=plugin.get("source", {}).get("resolved_commit"))
            for name, plugin in plugins.items()}


def refresh_skills(plugins):
    herdr_skill = subprocess.check_output(["herdr", "--skill"], text=True, timeout=15)
    viewer = plugins["herdr-file-viewer"]
    managed = viewer.get("source", {}).get("managed_path")
    if not managed:
        raise RuntimeError("Installed file viewer has no managed checkout")
    viewer_skill = (Path(managed) / "skills/herdr-file-viewer/SKILL.md").read_text()
    if not herdr_skill.strip() or not viewer_skill.strip():
        raise RuntimeError("Refusing to replace an agent skill with empty output")
    for name, content in (("herdr", herdr_skill), ("herdr-file-viewer", viewer_skill)):
        directory = Path.home() / ".agents/skills" / name
        directory.mkdir(parents=True, exist_ok=True)
        temporary = directory / ".SKILL.md.update"
        temporary.write_text(content)
        temporary.replace(directory / "SKILL.md")


def main():
    directory = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "herdr/plugin-updates"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_file = directory / f"{stamp}-{uuid.uuid4().hex[:8]}.json"
    report = dict(started_at=stamp, status="started", before={}, after={})
    with (directory / "update.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        save(report_file, report)
        try:
            report["herdr_version"] = subprocess.check_output(["herdr", "--version"], text=True, timeout=15).strip()
            report["before"] = revisions(inventory())
            save(report_file, report)
            for source in PLUGINS.values():
                print(f"Installing Herdr plugin: {source}", file=sys.stderr)
                subprocess.run(["herdr", "plugin", "install", source, "--yes"],
                               check=True, stdout=sys.stderr, timeout=180)
            installed = inventory()
            report["after"] = revisions(installed)
            for name in PLUGINS:
                if name not in installed or not installed[name].get("enabled"):
                    raise RuntimeError(f"Required plugin is missing or disabled: {name}")
                if installed[name].get("warnings"):
                    raise RuntimeError(f"Plugin {name} reports warnings: {installed[name]['warnings']}")
            refresh_skills(installed)
            report["status"] = "updated"
        except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
            report.update(status="failed", error=str(error))
            try:
                report["after"] = revisions(inventory())
            except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as after_error:
                report["after_error"] = str(after_error)
        save(report_file, report)
    print(json.dumps(dict(report=str(report_file), status=report["status"])))
    if report["status"] == "failed":
        print(f"Herdr plugin update failed: {report['error']}\nReport: {report_file}", file=sys.stderr)
        return 1
    print(f"Herdr plugins updated. Report: {report_file}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
