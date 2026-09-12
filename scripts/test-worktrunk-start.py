"""Run the creation hook in temporary repositories; never touch user worktrees."""
import json
import errno
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "dot_config/worktrunk/config.toml"
WT = shutil.which("wt")


class StartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.cleanup_repo)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "primary"
        # Commit hooks export repository-local variables such as GIT_INDEX_FILE.
        # They must not redirect Git operations in these independent fixtures.
        local_vars = subprocess.check_output(
            ["git", "rev-parse", "--local-env-vars"], text=True).splitlines()
        self.env = {key: value for key, value in os.environ.items() if key not in local_vars}
        self.env.update(GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com")
        self.git("init", "-q", "--initial-branch=main", str(self.repo), cwd=self.root)
        (self.repo / ".gitignore").write_text(".env.local\n.cache/\n.worktreeinclude\n")
        (self.repo / "tracked").write_text("base\n")
        self.git("add", ".")
        self.git("-c", "core.hooksPath=/dev/null", "commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        (self.repo / ".env.local").write_text("primary settings\n")
        (self.repo / ".cache").mkdir()
        (self.repo / ".cache/other").write_text("not selected\n")
        (self.repo / "untracked").write_text("not ignored\n")

    def cleanup_repo(self):
        # wt may finish background cache writes just after switch returns.
        for attempt in range(20):
            try:
                self.temp.cleanup()
                return
            except OSError as error:
                if error.errno != errno.ENOTEMPTY or attempt == 19:
                    raise
                time.sleep(0.1)

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.repo, env=self.env,
                              text=True, capture_output=True, check=True)

    def wt(self, *args, cwd=None, check=True, overrides=(), env=None):
        settings = [f'worktree-path = {json.dumps(str(self.root / "{{ branch }}"))}',
                    'pre-switch.fetch=""', 'post-switch.herdr=""',
                    'pre-remove.herdr=""', 'post-remove.herdr=""', *overrides]
        command = [WT, "--config", str(CONFIG)]
        for setting in settings:
            command.extend(["--config-set", setting])
        return subprocess.run([*command, *args], cwd=cwd or self.repo, env=env or self.env,
                              text=True, capture_output=True, check=check)

    def create(self, name, **kwargs):
        self.wt("switch", "--create", name, "--base", "main", "--no-cd", "--yes", **kwargs)
        return self.root / name

    def test_include_is_required(self):
        target = self.create("no-include")
        self.assertFalse((target / ".env.local").exists())

    def test_only_selected_ignored_files_copy_once_from_primary(self):
        (self.repo / ".worktreeinclude").write_text(".env.local\ntracked\nuntracked\n")
        first = self.create("first")
        self.assertEqual((first / ".env.local").read_text(), "primary settings\n")
        self.assertFalse((first / ".cache/other").exists())
        self.assertFalse((first / "untracked").exists())
        (first / ".env.local").write_text("worktree settings\n")
        second = self.create("second", cwd=first)
        self.assertEqual((second / ".env.local").read_text(), "primary settings\n")
        self.wt("step", "copy-ignored", "--require-include", cwd=first)
        self.assertEqual((first / ".env.local").read_text(), "worktree settings\n")
        (first / ".env.local").unlink()
        self.wt("switch", "first", "--no-cd", "--yes")
        self.assertFalse((first / ".env.local").exists(), "existing worktrees must not copy again")

    def test_explicit_base_is_preserved_with_same_named_remote(self):
        remote = self.git("commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "remote ahead").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/topic", remote)
        target = self.create("topic")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=target).stdout.strip(), self.base)
        result = subprocess.run(["git", "config", "--get", "branch.topic.remote"],
                                cwd=target, capture_output=True)
        self.assertEqual(result.returncode, 1)

    def test_copy_failure_stops_startup_and_keeps_created_worktree(self):
        # Fail the nested copy command; the outer wt is still the real binary.
        bindir = self.root / "bin"
        bindir.mkdir()
        stub = bindir / "wt"
        stub.write_text('#!/bin/sh\necho "copy I/O failure" >&2\nexit 1\n')
        stub.chmod(0o755)
        sentinel = self.root / "post-switch-ran"
        result = self.wt("switch", "--create", "failure", "--base", "main", "--no-cd", "--yes",
                         check=False, env=dict(self.env, PATH=f"{bindir}:{self.env['PATH']}"),
                         overrides=[f'post-switch.herdr = {json.dumps("touch " + str(sentinel))}'])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("copy I/O failure", result.stdout + result.stderr)
        self.assertTrue((self.root / "failure/.git").is_file())
        self.assertFalse(sentinel.exists())

    def test_remove_refuses_dirty_checkout(self):
        target = self.create("dirty")
        (target / "tracked").write_text("local changes\n")
        result = self.wt("remove", "--foreground", "--", str(target), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((target / "tracked").read_text(), "local changes\n")

    def test_remove_keeps_unmerged_branch(self):
        target = self.create("unmerged")
        (target / "tracked").write_text("unmerged work\n")
        self.git("add", "tracked", cwd=target)
        self.git("-c", "core.hooksPath=/dev/null", "commit", "-qm", "work", cwd=target)
        self.wt("remove", "--foreground", "--", str(target))
        self.assertFalse(target.exists())
        self.git("show-ref", "--verify", "refs/heads/unmerged")


if __name__ == "__main__":
    unittest.main()
