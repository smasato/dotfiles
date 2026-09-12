"""Confirm/cancel the removal popup with inert wt and fzf commands."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "dot_config/herdr/scripts/executable_worktree-remove.sh"


class RemoveTests(unittest.TestCase):
    def run_popup(self, answer="y\n", *, cancel=False, changed=False, fail=False,
                  schema=2, empty=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = str(root / "o'reilly $(touch injected)\tcheckout\n")
            def row(branch, path, main=False, detached=False):
                return dict(branch=branch, head={"sha": "abc"},
                            worktree=dict(path=path, main=main, detached=detached))
            items = [row("main", str(root), main=True), row(None, "/detached", detached=True)]
            if not empty:
                items.append(row("feature/o'reilly", path))
            (root / "snapshot").write_text(json.dumps(dict(schema=schema, items=items)))
            if changed and not empty:
                items[-1]["head"]["sha"] = "def"
            (root / "latest").write_text(json.dumps(dict(schema=schema, items=items)))
            wt = root / "wt"
            wt.write_text(f'''#!{sys.executable}
import json, pathlib, sys
root = pathlib.Path({str(root)!r})
args = sys.argv[1:]
with (root / "calls").open("a") as f: f.write(json.dumps(args) + "\\n")
if args == ["list", "--format=json"]:
    count = (root / "listed").exists()
    (root / "listed").touch()
    print((root / ("latest" if count else "snapshot")).read_text())
elif args[0] == "remove":
    assert pathlib.Path.cwd() == root.resolve()
    sys.exit({1 if fail else 0})
else: sys.exit(99)
''')
            wt.chmod(0o755)
            fzf = root / "fzf"
            fzf.write_text(f'''#!{sys.executable}
import pathlib, sys
rows = sys.stdin.read()
pathlib.Path({str(root / 'rows')!r}).write_text(rows)
if {cancel!r}: sys.exit(130)
print(rows.splitlines()[0])
''')
            fzf.chmod(0o755)
            result = subprocess.run(["bash", str(SCRIPT)], input=answer, text=True,
                                    capture_output=True, cwd=root,
                                    env=dict(os.environ, PATH=f"{root}:{os.environ['PATH']}"))
            calls = [json.loads(line) for line in (root / "calls").read_text().splitlines()]
            rows = (root / "rows").read_text() if (root / "rows").exists() else ""
            return result, calls, rows, path

    def test_confirmation_removes_exact_path_without_force(self):
        result, calls, rows, path = self.run_popup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [["list", "--format=json"], ["list", "--format=json"],
                                 ["remove", "--foreground", "--", path]])
        self.assertIn(json.dumps(path), result.stdout)
        self.assertNotIn("/detached", rows)
        self.assertNotIn("\tmain\t", rows)

    def test_cancel_and_default_no_never_remove(self):
        for options in ({"answer": "\n"}, {"answer": "no\n"}, {"answer": ""}, {"cancel": True}):
            with self.subTest(options=options):
                result, calls, _, _ = self.run_popup(**options)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(calls, [["list", "--format=json"]])

    def test_changed_target_requires_new_selection(self):
        result, calls, _, _ = self.run_popup(changed=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(call[0] == "remove" for call in calls))
        self.assertIn("changed while confirming", result.stderr)

    def test_removal_failure_stays_visible_without_retry(self):
        result, calls, _, _ = self.run_popup(fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sum(call[0] == "remove" for call in calls), 1)
        self.assertIn("Removal failed", result.stderr)

    def test_empty_or_unsupported_list_cannot_remove(self):
        for options in ({"schema": 1}, {"empty": True}):
            with self.subTest(options=options):
                result, calls, _, _ = self.run_popup(**options)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [["list", "--format=json"]])


if __name__ == "__main__":
    unittest.main()
