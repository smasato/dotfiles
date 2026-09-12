"""Plugin update inventory, failures, skill refresh, and task validation ordering."""
import importlib.util
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "dot_config/herdr/scripts/herdr_plugins.py"
STUB = r'''
import json, os, pathlib, sys
root=pathlib.Path(os.environ['FIXTURE'])
a=sys.argv[1:]
with (root/'calls').open('a') as f: f.write(json.dumps(a)+'\n')
f=root/'installed'
installed=json.loads(f.read_text()) if f.exists() else []
mode=os.environ.get('FAIL','')
names=['worktrunk','herdr-file-viewer','herdr-lazygit']
if a==['--version']: print('herdr 0.9.0')
elif a==['--skill']: print('new Herdr skill')
elif a==['plugin','list','--json']:
 if mode=='inventory': print('bad json'); sys.exit(0)
 plugins=[dict(plugin_id=name,enabled=True,version='new' if name in installed else 'old',
               source=dict(resolved_commit='new-sha' if name in installed else 'old-sha',managed_path=str(root/'viewer')),
               warnings=['incompatible'] if mode=='warning' and installed else []) for name in names]
 print(json.dumps({'ok':True,'result':{'plugins':plugins}}))
elif a[:2]==['plugin','install']:
 name=dict(zip(['devashish2203/herdr-worktrunk','smarzban/herdr-file-viewer','crokily/herdr-lazygit'],names))[a[2]]
 assert a[3:]==['--yes']
 if mode=='install' and name=='herdr-file-viewer': sys.exit(1)
 installed.append(name); f.write_text(json.dumps(installed))
else: sys.exit('Unexpected argv '+repr(a))
'''


class HerdrPluginTests(unittest.TestCase):
    def run_update(self, failure=""):
        temporary = tempfile.TemporaryDirectory(prefix="herdr plugin update ")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        stub = root / "herdr"
        stub.write_text(f"#!{sys.executable}\n{STUB}")
        stub.chmod(0o755)
        viewer = root / "viewer/skills/herdr-file-viewer/SKILL.md"
        viewer.parent.mkdir(parents=True)
        if failure != "skill":
            viewer.write_text("new viewer skill")
        for name in ("herdr", "herdr-file-viewer"):
            skill = root / ".agents/skills" / name / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("old skill")
        result = subprocess.run([sys.executable, str(SCRIPT)], text=True, capture_output=True,
                                env=dict(os.environ, HOME=str(root), XDG_STATE_HOME=str(root / "state"),
                                         FIXTURE=str(root), FAIL=failure, PATH=f"{root}:{os.environ['PATH']}"))
        output = json.loads(result.stdout)
        report = json.loads(Path(output["report"]).read_text())
        calls = [json.loads(line) for line in (root / "calls").read_text().splitlines()]
        return root, result, report, calls

    def test_update_records_revisions_and_refreshes_skills(self):
        root, result, report, calls = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "updated")
        self.assertEqual(report["before"]["worktrunk"]["commit"], "old-sha")
        self.assertEqual(report["after"]["worktrunk"]["commit"], "new-sha")
        self.assertEqual(len([a for a in calls if a[:2] == ["plugin", "install"]]), 3)
        self.assertEqual((root / ".agents/skills/herdr/SKILL.md").read_text(), "new Herdr skill\n")
        self.assertEqual((root / ".agents/skills/herdr-file-viewer/SKILL.md").read_text(), "new viewer skill")

    def test_failures_are_recorded_without_replacing_skills(self):
        for failure in ("inventory", "install", "skill", "warning"):
            with self.subTest(failure=failure):
                root, result, report, calls = self.run_update(failure)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(report["status"], "failed")
                self.assertIn("error", report)
                self.assertEqual((root / ".agents/skills/herdr/SKILL.md").read_text(), "old skill")
                if failure == "inventory":
                    self.assertFalse(any(a[:2] == ["plugin", "install"] for a in calls))
                if failure == "install":
                    self.assertEqual(report["after"]["worktrunk"]["commit"], "new-sha")
                    self.assertEqual(report["after"]["herdr-file-viewer"]["commit"], "old-sha")

    def test_chezmoi_entrypoint_uses_shared_installer(self):
        rendered = subprocess.check_output(["chezmoi", "execute-template", "--file",
                                           str(ROOT / ".chezmoiscripts/run_onchange_after_herdr-plugins.sh.tmpl")], text=True)
        subprocess.run(["shellcheck", "-"], input=rendered, text=True, check=True)
        with tempfile.TemporaryDirectory(prefix="herdr home ") as directory:
            home = Path(directory)
            script = home / ".config/herdr/scripts/update-plugins.sh"
            script.parent.mkdir(parents=True)
            script.write_text('#!/bin/sh\nprintf shared-installer\n')
            result = subprocess.check_output(["bash"], input=rendered, text=True,
                                             env=dict(os.environ, HOME=str(home)))
            self.assertEqual(result, "shared-installer")

    def test_manual_task_checks_before_and_after(self):
        spec = importlib.util.spec_from_file_location("update_herdr_plugins", ROOT / "scripts/update-herdr-plugins.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for failure in ("", "before", "installer", "after"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                report = Path(directory) / "report.json"
                report.write_text(json.dumps({"status": "failed" if failure == "installer" else "updated"}))
                calls = []
                def run(argv, **kwargs):
                    stage = "installer" if argv[0] == "bash" else "before" if not calls else "after"
                    calls.append(stage)
                    code = 1 if stage == failure else 0
                    if code and kwargs.get("check"):
                        raise subprocess.CalledProcessError(code, argv)
                    return subprocess.CompletedProcess(argv, code, stdout=json.dumps({"report": str(report)}))
                with patch.object(module.subprocess, "run", side_effect=run), redirect_stdout(io.StringIO()):
                    if failure == "before":
                        with self.assertRaises(subprocess.CalledProcessError): module.main()
                        self.assertEqual(calls, ["before"])
                    else:
                        self.assertEqual(module.main(), int(bool(failure)))
                        self.assertEqual(calls, ["before", "installer"] if failure == "installer" else ["before", "installer", "after"])
                        if failure != "installer":
                            self.assertEqual(json.loads(report.read_text())["status"], "validation-failed" if failure else "verified")
                        else:
                            saved = json.loads(report.read_text())
                            self.assertEqual(saved["status"], "failed")
                            self.assertEqual(saved["validation"], {"before": "passed", "after": "not-run"})


if __name__ == "__main__":
    unittest.main()
