"""Install/inspect isolated Codex homes through CLI stubs; never contact a marketplace."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STUB = r'''
import json, os, pathlib, sys
args = sys.argv[1:]
kind = pathlib.Path(sys.argv[0]).name
home = pathlib.Path(os.environ.get("CODEX_HOME", os.environ["HOME"])) if kind == "codex" else pathlib.Path(
    os.environ.get("CLAUDE_CONFIG_DIR", str(pathlib.Path(os.environ["HOME"]) / ".claude")))
assert home.parent == pathlib.Path(os.environ["HOME"])
with open(os.environ["LOG"], "a") as f: f.write(json.dumps([home.name, args]) + "\n")
mode = os.environ["MODE"]
if mode == "offline": sys.exit(1)
if kind == "claude":
    assert args == ["plugin", "list", "--json"]
    print(json.dumps([dict(id="worktrunk@worktrunk", scope="user", enabled=True)]))
elif args == ["plugin", "marketplace", "list", "--json"]:
    print(json.dumps(dict(marketplaces=[dict(name="worktrunk")] if (home / "marketplace").exists() else [])))
elif args == ["plugin", "marketplace", "add", "max-sixty/worktrunk"]:
    (home / "marketplace").touch()
elif args == ["plugin", "add", "worktrunk@worktrunk"]:
    if mode != "missing-after-install": (home / "installed").touch()
elif args == ["plugin", "list", "--marketplace", "worktrunk", "--json"]:
    print(json.dumps(dict(installed=[dict(pluginId="worktrunk@worktrunk", installed=True, enabled=True)]
                          if (home / "installed").exists() else [], available=[])))
else: sys.exit("Unexpected command: " + repr(args))
'''


class CodexPluginTests(unittest.TestCase):
    def fixture(self, root, mode):
        for name in ("mise", "codex", "claude"):
            path = root / name
            path.write_text("#!/bin/sh\nexit 0\n" if name == "mise" else f"#!{sys.executable}\n{STUB}")
            path.chmod(0o755)
        for name in (".claude", ".claude_work", ".codex", ".codex_work1", ".codex_work2", ".codex_work3"):
            home = root / name
            home.mkdir()
            (home / "config.toml").write_text('[plugins."worktrunk@worktrunk"]\nenabled = true\n')
        return dict(os.environ, HOME=str(root), MODE=mode, LOG=str(root / "calls"),
                    PATH=f"{root}:{os.environ['PATH']}", CODEX_HOME="inherited-wrong-home",
                    CLAUDE_CONFIG_DIR="inherited-wrong-home")

    def test_install_verify_and_preserve_disabled_homes(self):
        rendered = subprocess.check_output([
            "chezmoi", "execute-template", "--override-data", '{"work":true}', "--file",
            str(ROOT / ".chezmoiscripts/run_onchange_after_05-codex-worktrunk.sh.tmpl")], text=True)
        subprocess.run(["shellcheck", "-"], input=rendered, text=True, check=True)
        for mode in ("fresh", "offline", "missing-after-install"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                env = self.fixture(root, mode)
                (root / ".codex_work2/config.toml").write_text(
                    '[plugins."worktrunk@worktrunk"]\nenabled = false\n')
                script = rendered.replace('export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"',
                                          "export PATH=" + shlex.quote(env["PATH"]))
                result = subprocess.run(["/bin/bash"], input=script, text=True, env=env, capture_output=True)
                if mode != "fresh":
                    self.assertNotEqual(result.returncode, 0)
                    continue
                self.assertEqual(result.returncode, 0, result.stderr)
                for name in (".codex", ".codex_work1", ".codex_work3"):
                    self.assertTrue((root / name / "installed").exists())
                self.assertFalse((root / ".codex_work2/installed").exists())
                # A second execution verifies state without reinstalling any home.
                (root / "calls").write_text("")
                subprocess.run(["/bin/bash"], input=script, text=True, env=env, capture_output=True, check=True)
                calls = [json.loads(line) for line in (root / "calls").read_text().splitlines()]
                self.assertEqual({home for home, args in calls}, {".codex", ".codex_work1", ".codex_work3"})
                self.assertFalse(any("add" in args for home, args in calls))

    def test_read_only_check_visits_each_home_and_reports_missing_plugins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = self.fixture(root, "fresh")
            command = [sys.executable, str(ROOT / "scripts/check-worktrunk-plugins.py")]
            result = subprocess.run(command, env=env, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".codex_work3: missing or disabled", result.stdout)
            for home in root.glob(".codex*"):
                (home / "installed").touch()
            result = subprocess.run(command, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in (root / "calls").read_text().splitlines()]
            self.assertEqual({home for home, args in calls},
                             {".claude", ".claude_work", ".codex", ".codex_work1", ".codex_work2", ".codex_work3"})
            self.assertTrue(all("list" in args for home, args in calls))


if __name__ == "__main__":
    unittest.main()
