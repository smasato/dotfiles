"""Exercise actual wt template expansion with inert command stubs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "dot_config/worktrunk/config.toml"


class HookTests(unittest.TestCase):
    def run_hook(self, hook, **variables):
        result = subprocess.run(
            ["wt", "--config", str(CONFIG), "hook", hook, "--dry-run",
             *(f"--{key.replace('_', '-')}={value}" for key, value in variables.items())],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        command = "\n".join(line[2:] for line in (result.stdout + result.stderr).splitlines()
                            if line.startswith("  "))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "argv.jsonl"
            for name in ("git", "bash", "pueue"):
                stub = root / name
                stub.write_text(f"#!{sys.executable}\nimport json,sys\n"
                                f"with open({str(log)!r},'a') as f: "
                                "f.write(json.dumps(sys.argv[1:])+'\\n')\n")
                stub.chmod(0o755)
            subprocess.run(["shellcheck", "-s", "sh", "-e", "SC2016,SC2050", "-"], input=command,
                           text=True, check=True, capture_output=True)
            subprocess.run(["/bin/sh", "-c", command], check=True,
                           env=dict(os.environ, PATH=f"{root}:{os.environ['PATH']}"))
            return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    def test_branch_quotes_and_metacharacters(self):
        for branch in ("feature/o'reilly", 'feature/$(touch-injected);x'):
            with self.subTest(branch=branch):
                self.assertEqual(self.run_hook("pre-switch", branch=branch),
                                 [["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"]])
                self.assertEqual(self.run_hook("pre-start", branch=branch, upstream=""), [
                    ["rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
                    ["branch", "--set-upstream-to", f"origin/{branch}"],
                    ["merge", "--ff-only", f"origin/{branch}"],
                ])

    def test_paths_and_detached_label(self):
        path = "/tmp/wt audit/o'reilly"
        variables = dict(worktree_path=path, primary_worktree_path=path,
                         repo_path="/tmp/repo root", branch="", short_commit="abc1234")
        self.assertEqual(self.run_hook("post-switch", **variables), [])
        variables["primary_worktree_path"] = "/tmp/main"
        calls = self.run_hook("post-switch", **variables)
        self.assertEqual(calls[0][-3:], ["/tmp/repo root", path, "abc1234"])

    def test_detached_skips_git_hooks(self):
        for hook in ("pre-switch", "pre-start"):
            self.assertEqual(self.run_hook(hook, branch=""), [])

    def test_upstream_and_remove_paths(self):
        upstream = "mirror/o'reilly"
        self.assertEqual(self.run_hook("pre-start", branch="topic", upstream=upstream),
                         [["merge", "--ff-only", upstream]])
        path = "/tmp/o'reilly worktree"
        for hook, action in (("pre-remove", "capture"), ("post-remove", "queue-close")):
            self.assertEqual(self.run_hook(hook, worktree_path=path)[0][-2:], [action, path])


if __name__ == "__main__":
    unittest.main()
