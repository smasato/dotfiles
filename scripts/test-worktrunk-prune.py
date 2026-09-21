"""wt-prune end-to-end regressions on real git/wt fixtures with a stubbed forge.

Every test builds a temporary repository, creates worktrees only through wt,
and runs dot_config/worktrunk/prune.py as a subprocess. The gh CLI is a stub;
git and wt are real. No user worktree, config, or network is ever touched.
"""
import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PRUNE = ROOT / "dot_config/worktrunk/prune.py"
WT = shutil.which("wt")
REPO_URL = "https://github.com/example/repo"
ORIGIN = "git@github.com:example/repo.git"

# Forge answers come from the environment so each test controls PR state.
GH_STUB = '''
import json, os, sys
args = sys.argv[1:]
if os.environ.get("GH_STUB_FAIL"):
    sys.exit(1)
if args[:2] == ["repo", "view"]:
    print(json.dumps({"url": os.environ["GH_STUB_REPO"]}))
elif args[:2] == ["pr", "list"]:
    print(os.environ.get("GH_STUB_PRS", "[]"))
else:
    sys.exit("unexpected gh command: " + repr(args))
'''

# Pass-through wt wrapper: during `wt remove`, advances the
# other candidate's HEAD to exercise the pre-removal recheck deterministically.
WT_WRAPPER = '''
import os, pathlib, subprocess, sys
args = sys.argv[1:]
skip = False
subcommand = ""
for arg in args:
    if skip:
        skip = False
        continue
    if arg in ("--config", "--config-set"):
        skip = True
        continue
    if not arg.startswith("-"):
        subcommand = arg
        break
if subcommand == "remove":
    target = pathlib.Path(args[-1]).resolve() if args and args[-1] != "--" else None
    for entry in os.environ.get("WT_RACE_DIRS", "").split(os.pathsep):
        directory = pathlib.Path(entry) if entry else None
        if directory and directory.is_dir() and directory.resolve() != target:
            subprocess.run(["git", "-C", str(directory), "commit", "--allow-empty",
                            "-qm", "raced"], check=True)
os.execv(os.environ["REAL_WT"], ["wt", *args])
'''


class PruneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wt-prune-test-")
        self.addCleanup(self.cleanup_repo)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "primary"
        self.home = self.root / "home"
        self.home.mkdir()
        bindir = self.root / "bin"
        bindir.mkdir()
        gh = bindir / "gh"
        gh.write_text(f"#!{sys.executable}\n{GH_STUB}")
        gh.chmod(0o755)
        # An otherwise empty wt config; only the worktree location is pinned.
        self.config = self.root / "wt.toml"
        self.config.write_text(
            f'worktree-path = {json.dumps(str(self.root / "{{ branch }}"))}\n')
        # Commit hooks export repository-local variables such as GIT_INDEX_FILE.
        # They must not redirect Git operations in these independent fixtures.
        local_vars = subprocess.check_output(
            ["git", "rev-parse", "--local-env-vars"], text=True).splitlines()
        self.env = {key: value for key, value in os.environ.items()
                    if key not in local_vars}
        # Fixture commits must not inherit user hooks, signing, system config,
        # or the real gh/wt user configuration.
        self.env.update(
            GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
            GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
            GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com",
            HOME=str(self.home),
            XDG_CONFIG_HOME=str(self.home / "config"),
            XDG_DATA_HOME=str(self.home / "data"),
            XDG_CACHE_HOME=str(self.home / "cache"),
            PATH=f"{bindir}:{os.environ['PATH']}",
            GH_STUB_REPO=REPO_URL)
        self.git("init", "-q", "--initial-branch=main", str(self.repo),
                 cwd=self.root)
        (self.repo / "tracked").write_text("base\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")

    def cleanup_repo(self):
        # wt may finish background cache writes just after a command returns.
        for attempt in range(20):
            try:
                self.temp.cleanup()
                return
            except OSError as error:
                if error.errno != errno.ENOTEMPTY or attempt == 19:
                    raise
                time.sleep(0.1)

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(["git", *args], cwd=cwd or self.repo, env=self.env,
                              text=True, capture_output=True, check=check)

    def wt(self, *args, cwd=None, check=True):
        return subprocess.run([WT, "--config", str(self.config), *args],
                              cwd=cwd or self.repo, env=self.env,
                              text=True, capture_output=True, check=check)

    def create(self, name, base="main"):
        self.wt("switch", "--create", name, "--base", base, "--no-cd", "--yes")
        return self.root / name

    def commit_in(self, path, filename):
        (path / filename).write_text(f"{filename} contents\n")
        self.git("add", filename, cwd=path)
        self.git("commit", "-qm", f"add {filename}", cwd=path)

    def wt_merge(self, path):
        """Merge through wt (commit/squash/rebase/ff), keeping worktree+branch."""
        self.wt("merge", "--no-remove", "--no-hooks", "--yes", cwd=path)

    def squash_merge(self, branch):
        """Reproduce a forge squash merge: content lands on main, branch stays."""
        self.git("merge", "--squash", "-q", branch)
        self.git("commit", "-qm", f"squash {branch}")

    def track(self, branch, remote_branch=None):
        """Give a local branch an upstream so the PR check can resolve it."""
        remote_branch = remote_branch or branch
        self.git("config", f"branch.{branch}.remote", "origin")
        self.git("config", f"branch.{branch}.merge",
                 f"refs/heads/{remote_branch}")
        self.git("update-ref", f"refs/remotes/origin/{remote_branch}", branch)

    def pull(self, number=7, branch="topic", sha="current", state="OPEN",
             owner="example", name="repo"):
        return dict(number=number, state=state, headRefName=branch,
                    headRefOid=sha,
                    headRepository=dict(name=name) if name else None,
                    headRepositoryOwner=dict(login=owner),
                    url=f"{REPO_URL}/pull/{number}")

    def prs_env(self, prs):
        return dict(self.env, GH_STUB_PRS=json.dumps(prs))

    def run_prune(self, *args, cwd=None, env=None, check=True):
        return subprocess.run(
            [sys.executable, str(PRUNE), "--config", str(self.config), *args],
            cwd=cwd or self.repo, env=env or self.env,
            text=True, capture_output=True, check=check)

    def dry_run(self, **kwargs):
        result = self.run_prune("--dry-run", "--format=json", **kwargs)
        candidates = json.loads(result.stdout)
        self.assertIsInstance(candidates, list)
        return candidates, result

    def branch_exists(self, name):
        return self.git("show-ref", "--verify", "--quiet",
                        f"refs/heads/{name}", check=False).returncode == 0

    def install_wt_wrapper(self, **env):
        wrapper = self.root / "bin" / "wt"
        wrapper.write_text(f"#!{sys.executable}\n{WT_WRAPPER}")
        wrapper.chmod(0o755)
        return dict(self.env, REAL_WT=WT, **env)

    def test_fresh_worktrees_are_retained_even_from_staging(self):
        # staging is squash-merged into main, so a worktree created from it is
        # a content-integrated prune candidate. With no commits of its own it
        # must still be kept: the creation record proves no work happened.
        self.git("checkout", "-q", "-b", "staging")
        (self.repo / "staged.txt").write_text("staged\n")
        self.git("add", ".")
        self.git("commit", "-qm", "staged")
        self.git("checkout", "-q", "main")
        self.squash_merge("staging")
        fresh_main = self.create("fresh-main")
        fresh_staging = self.create("fresh-staging", base="staging")
        candidates, result = self.dry_run()
        branches = [candidate["branch"] for candidate in candidates]
        self.assertNotIn("fresh-main", branches)
        self.assertNotIn("fresh-staging", branches)
        result = self.run_prune("--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name, path in (("fresh-main", fresh_main),
                           ("fresh-staging", fresh_staging)):
            self.assertTrue(path.is_dir(), name)
            self.assertTrue(self.branch_exists(name), name)

    def test_same_day_merged_worktrees_are_removed_live(self):
        for name in ("merged-ff", "merged-squash"):
            self.commit_in(self.create(name), f"{name}.txt")
        self.wt_merge(self.root / "merged-ff")
        self.squash_merge("merged-squash")
        candidates, _ = self.dry_run()
        self.assertEqual({candidate["branch"] for candidate in candidates},
                         {"merged-ff", "merged-squash"})
        result = self.run_prune("--yes", "--format=json")
        self.assertEqual({row["branch"] for row in json.loads(result.stdout)},
                         {"merged-ff", "merged-squash"})
        for name in ("merged-ff", "merged-squash"):
            self.assertFalse((self.root / name).exists(), name)
            self.assertFalse(self.branch_exists(name), name)

    def test_uncertain_pr_states_retain_integrated_branch(self):
        self.git("remote", "add", "origin", ORIGIN)
        path = self.create("pr-branch")
        self.commit_in(path, "pr.txt")
        self.squash_merge("pr-branch")
        # The PR is matched on the upstream branch name, not the local one.
        self.track("pr-branch", "pr-branch-remote")
        head = self.git("rev-parse", "pr-branch").stdout.strip()
        cases = {
            "open": [self.pull(branch="pr-branch-remote", sha=head)],
            "closed": [self.pull(branch="pr-branch-remote", sha=head,
                                 state="CLOSED")],
            "head-mismatch": [self.pull(branch="pr-branch-remote",
                                        sha="0" * 40, state="MERGED")],
            "two-open": [self.pull(7, branch="pr-branch-remote", sha=head),
                         self.pull(8, branch="pr-branch-remote", sha=head)],
            "deleted-fork": [self.pull(branch="pr-branch-remote", sha=head,
                                       state="MERGED", name=None)],
        }
        for name, prs in cases.items():
            with self.subTest(case=name):
                self.run_prune("--yes", env=self.prs_env(prs))
                self.assertTrue(path.is_dir())
                self.assertTrue(self.branch_exists("pr-branch"))
        for name, extra in (("gh-failure", {"GH_STUB_FAIL": "1"}),
                            ("gh-malformed", {"GH_STUB_PRS": "not json"})):
            with self.subTest(case=name):
                self.run_prune("--yes", env=dict(self.env, **extra))
                self.assertTrue(path.is_dir())
                self.assertTrue(self.branch_exists("pr-branch"))
        # Control: a confirmed empty PR list makes the same branch eligible.
        candidates, _ = self.dry_run(env=self.prs_env([]))
        self.assertIn("pr-branch",
                      [candidate["branch"] for candidate in candidates])
        self.assertTrue(path.is_dir())
        self.assertTrue(self.branch_exists("pr-branch"))

    def test_exact_merged_pr_is_removed(self):
        self.git("remote", "add", "origin", ORIGIN)
        path = self.create("merged-pr")
        self.commit_in(path, "merged.txt")
        self.squash_merge("merged-pr")
        self.track("merged-pr")
        head = self.git("rev-parse", "merged-pr").stdout.strip()
        env = self.prs_env([self.pull(11, branch="merged-pr", sha=head,
                                    state="MERGED")])
        result = self.run_prune("--yes", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(path.exists())
        self.assertFalse(self.branch_exists("merged-pr"))

    def test_fresh_branch_wins_over_matching_merged_pr(self):
        # An old MERGED PR matching name and head must not beat the creation
        # check: the branch was just created and no work happened on it.
        self.git("remote", "add", "origin", ORIGIN)
        path = self.create("reused")
        head = self.git("rev-parse", "reused").stdout.strip()
        self.track("reused")
        candidates, _ = self.dry_run(env=self.prs_env(
            [self.pull(3, branch="reused", sha=head, state="MERGED")]))
        self.assertNotIn("reused",
                         [candidate["branch"] for candidate in candidates])
        self.assertTrue(path.is_dir())
        self.assertTrue(self.branch_exists("reused"))

    def test_missing_creation_reflog_retains(self):
        path = self.create("merged")
        self.commit_in(path, "m.txt")
        self.squash_merge("merged")
        self.git("reflog", "expire", "--expire=now", "refs/heads/merged")
        candidates, result = self.dry_run()
        self.assertNotIn("merged",
                         [candidate["branch"] for candidate in candidates])
        self.assertTrue(path.is_dir())
        self.assertTrue(self.branch_exists("merged"))

    def test_no_remote_repo_prunes_without_gh(self):
        # With no configured remote there is no forge identity to check; the
        # local integration + creation-change rule applies even if gh fails.
        path = self.create("local-only")
        self.commit_in(path, "l.txt")
        self.squash_merge("local-only")
        result = self.run_prune("--yes", env=dict(self.env, GH_STUB_FAIL="1"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(path.exists())
        self.assertFalse(self.branch_exists("local-only"))

    def test_uncertain_remote_identity_retains(self):
        # A remote whose URL cannot be tied to the forge stays unknown.
        self.git("remote", "add", "origin", str(self.root / "peer.git"))
        path = self.create("unclear")
        self.commit_in(path, "u.txt")
        self.squash_merge("unclear")
        self.track("unclear")
        candidates, result = self.dry_run()
        self.assertNotIn("unclear",
                         [candidate["branch"] for candidate in candidates])
        self.assertTrue(path.is_dir())
        self.assertTrue(self.branch_exists("unclear"))

    def test_branch_only_candidates_follow_same_rules(self):
        # Eligible: changed since creation, integrated, confirmed no PR.
        self.git("checkout", "-q", "-b", "merged-branch")
        (self.repo / "mb.txt").write_text("mb\n")
        self.git("add", ".")
        self.git("commit", "-qm", "mb")
        self.git("checkout", "-q", "main")
        self.squash_merge("merged-branch")
        # Retained: a branch-only ref with no work since creation.
        self.git("branch", "fresh-branch", "main")
        candidates, _ = self.dry_run()
        branches = [candidate["branch"] for candidate in candidates]
        self.assertIn("merged-branch", branches)
        self.assertNotIn("fresh-branch", branches)
        result = self.run_prune("--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.branch_exists("merged-branch"))
        self.assertTrue(self.branch_exists("fresh-branch"))

    def test_dirty_worktree_is_never_removed(self):
        path = self.create("dirty")
        self.commit_in(path, "d.txt")
        self.squash_merge("dirty")
        (path / "uncommitted.txt").write_text("unsaved\n")
        result = self.run_prune("--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(path.is_dir())
        self.assertTrue((path / "uncommitted.txt").exists())
        self.assertTrue(self.branch_exists("dirty"))

    def test_head_change_before_removal_aborts_that_candidate(self):
        # The wrapper commits to the other candidate during each wt remove, so
        # whichever is processed second must be held by the recheck.
        for name in ("race-a", "race-b"):
            self.commit_in(self.create(name), f"{name}.txt")
            self.squash_merge(name)
        env = self.install_wt_wrapper(WT_RACE_DIRS=os.pathsep.join(
            str(self.root / name) for name in ("race-a", "race-b")))
        result = self.run_prune("--yes", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        survivors = [name for name in ("race-a", "race-b")
                     if (self.root / name).exists()]
        removed = [name for name in ("race-a", "race-b")
                   if not (self.root / name).exists()]
        self.assertEqual(len(removed), 1, result.stderr)
        self.assertEqual(len(survivors), 1, result.stderr)
        survivor = survivors[0]
        self.assertTrue(self.branch_exists(survivor))
        self.assertFalse(self.branch_exists(removed[0]))
        self.assertIn("raced", self.git("log", "-1", "--format=%s",
                                        survivor).stdout)

    def test_current_worktree_removed_last_with_cd_directive(self):
        for name in ("first", "current"):
            self.commit_in(self.create(name), f"{name}.txt")
            self.squash_merge(name)
        directive = self.root / "directive"
        env = dict(self.env, WORKTRUNK_DIRECTIVE_CD_FILE=str(directive))
        result = self.run_prune("--yes", cwd=self.root / "current", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "first").exists())
        self.assertFalse((self.root / "current").exists())
        # The shell integration must land the user back in the primary.
        self.assertEqual(Path(directive.read_text().strip()).resolve(),
                         self.repo)

    def test_dry_run_preview_removes_nothing(self):
        path = self.create("merged")
        self.commit_in(path, "m.txt")
        self.squash_merge("merged")
        # -C selects the repository from outside it.
        result = self.run_prune("--dry-run", "-C", str(self.repo),
                                cwd=self.root)
        self.assertIn("merged", result.stdout)
        self.assertTrue(path.is_dir())
        self.assertTrue(self.branch_exists("merged"))

    def test_unsupported_options_fail_closed(self):
        path = self.create("merged")
        self.commit_in(path, "m.txt")
        self.squash_merge("merged")
        for option in ("--min-age=0s", "--force", "-D", "--no-hooks"):
            with self.subTest(option=option):
                result = self.run_prune(option, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(path.is_dir())
                self.assertTrue(self.branch_exists("merged"))


if __name__ == "__main__":
    unittest.main()
