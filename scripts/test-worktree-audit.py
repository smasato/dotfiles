"""Check prune annotations without changing worktrees or contacting a forge."""

import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "dot_agents/skills/poteto-mode/scripts/executable_worktree-audit.sh"

STUB = r'''
import json, os, pathlib, sys
args = sys.argv[1:]
name = pathlib.Path(sys.argv[0]).name
root = pathlib.Path(os.environ["FIXTURE"])
if name in ("date", "stat"):
    sys.exit("BSD date/stat must use their system paths")
if name == "wt":
    with (root / "calls.jsonl").open("a") as log:
        log.write(json.dumps(args) + "\n")
    if args == ["list", "--format=json"]:
        print((root / "list.json").read_text())
    elif args == ["step", "prune", "--dry-run", "--min-age=2d", "--format=json"]:
        if os.environ["PREVIEW"] == "failed":
            sys.exit(1)
        print((root / "prune.json").read_text())
    else:
        sys.exit("unexpected wt command: " + repr(args))
elif name == "herdr":
    assert args == ["api", "snapshot"]
    with (root / "herdr-calls").open("a") as log: log.write("snapshot\n")
    if os.environ["HERDR_TEST"] == "failed": sys.exit(1)
    print((root / "herdr.json").read_text())
elif name == "gh":
    if os.environ["FAILURE"] == "gh": sys.exit(1)
    if os.environ["FAILURE"] == "gh-malformed": print("{}"); sys.exit(0)
    if args == ["repo", "view", "--json", "url"]:
        print(json.dumps({"url": "https://github.com/example/repo"}))
    else:
        assert args[:5] == ["pr", "list", "--repo", "https://github.com/example/repo", "--state"]
        print(json.dumps([{"number": 7, "state": "OPEN", "headRefName": "open", "headRefOid": "open",
                          "headRepository": {"name": "repo"}, "headRepositoryOwner": {"login": "example"},
                          "url": "https://github.com/example/repo/pull/7"}]))
elif name == "git":
    if args[:1] == ["-C"]:
        branch = pathlib.Path(args[1]).name
        args = args[2:]
    else:
        branch = "main"
    if args[:2] == ["merge-base", "--is-ancestor"]:
        if os.environ["FAILURE"] == "ancestry" and args[2] == "excluded": sys.exit(128)
        sys.exit(1 if args[2] == "integrated" else 0)
    elif args == ["status", "--porcelain"]:
        if os.environ["FAILURE"] == "status" and branch == "excluded": sys.exit(128)
        print(" M tracked.txt" if branch == "wip" else "", end="")
    elif args[:3] == ["remote", "get-url", "--"]:
        print("git@github.com:example/repo.git")
    else:
        sys.exit("unexpected git command: " + repr(args))
'''


class WorktreeAuditTests(unittest.TestCase):
    def run_audit(self, preview="available", failure="", herdr="available"):
        with tempfile.TemporaryDirectory(prefix="worktree-audit-test-") as directory:
            root = Path(directory).resolve()
            bindir = root / "bin"
            bindir.mkdir()
            for name in ("wt", "git", "gh", "herdr", "date", "stat"):
                command = bindir / name
                command.write_text(f"#!{sys.executable}\n{STUB}")
                command.chmod(0o755)

            branches = ("main", "integrated", "wip", "open", "recent", "unknown", "excluded")
            paths = {branch: root / branch for branch in branches}
            for path in paths.values():
                path.mkdir()
            (root / "list.json").write_text(json.dumps({
                "schema": 2, "repo": {"default_branch": "main"},
                "items": [{"branch": None if branch == "excluded" else branch,
                    "marker": "🤖" if branch == "integrated" else "💬" if branch == "open" else None,
                    "head": {"sha": branch, "committed_at": "2020-09-13T12:26:40Z"},
                    "upstream": {"remote": "mirror", "branch": "renamed", "ahead": 2, "behind": 3}
                    if branch == "integrated" else {"remote": "origin", "branch": branch, "ahead": 0, "behind": 2}
                    if branch in ("recent", "open", "wip", "main") else None, "worktree": {
                    "path": str(path), "main": branch == "main", "detached": branch == "excluded"
                }} for branch, path in paths.items()],
            }))
            alias = root / "alias"
            alias.symlink_to(paths["integrated"], target_is_directory=True)
            (root / "herdr.json").write_text(json.dumps({"ok": True, "result": {"snapshot": {"workspaces": [
                {"workspace_id": "w7", "worktree": {"checkout_path": str(alias)}},
                {"workspace_id": "w8", "worktree": {"checkout_path": str(paths["integrated"])}},
            ]}}}))
            candidates = [{
                "branch": branch, "path": str(paths[branch]), "kind": "worktree",
                "branch_deleted": branch != "integrated",
                "reason": "integrated into", "target": "main",
            } for branch in branches if branch not in ("main", "excluded")]
            candidates.append({"branch": "orphan", "path": None, "kind": "branch_only",
                               "branch_deleted": True, "reason": "same commit as", "target": "main"})
            payload = json.dumps(candidates)
            if preview == "malformed":
                payload = "not json"
            elif preview == "wrong-schema":
                payload = json.dumps({"items": candidates})
            elif preview == "empty":
                payload = "[]"
            (root / "prune.json").write_text(payload)

            transcripts = root / "transcripts"
            transcripts.mkdir()
            for branch in ("integrated", "recent", "excluded"):
                transcript = transcripts / f"{branch}.json"
                transcript.write_text(json.dumps({"path": str(paths[branch]) + "/file"}))
                age = 0 if branch == "recent" else 10 * 86400
                timestamp = time.time() - age
                os.utime(transcript, (timestamp, timestamp))

            result = subprocess.run(
                ["bash", str(AUDIT), str(paths["main"]), str(transcripts)],
                env=dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}",
                         FIXTURE=str(root), PREVIEW=preview, FAILURE=failure,
                         HERDR_TEST=herdr, HERDR_ENV="0" if herdr == "outside" else "1"),
                text=True, capture_output=True, check=True,
            )
            calls = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
            self.assertEqual(calls, [
                ["list", "--format=json"],
                ["step", "prune", "--dry-run", "--min-age=2d", "--format=json"],
            ])
            if herdr == "outside":
                self.assertFalse((root / "herdr-calls").exists())
            else:
                self.assertEqual((root / "herdr-calls").read_text(), "snapshot\n")
            rows = {Path(row["WORKTREE"]).name: row
                    for row in csv.DictReader(io.StringIO(result.stdout), delimiter="\t")}
            self.assertEqual(set(rows), set(branches) - {"main"})
            expected_buckets = {
                "integrated": "review", "wip": "hold-wip", "open": "hold-open-pr",
                "recent": "verify-recent-chat", "unknown": "hold-unknown",
                "excluded": "hold-unknown",
            }
            if failure.startswith("gh"):
                expected_buckets = {name: "hold-wip" if name == "wip" else "hold-unknown" for name in expected_buckets}
            elif failure:
                expected_buckets["excluded"] = "hold-unknown"
            self.assertEqual({name: row["BUCKET"] for name, row in rows.items()}, expected_buckets)
            return rows, result.stderr

    def test_snapshot_upstream_and_herdr_paths(self):
        rows, _ = self.run_audit()
        self.assertEqual(rows["integrated"]["REMOTE"], "mirror/renamed:+2/-3")
        self.assertEqual(rows["recent"]["REMOTE"], "origin/recent:+0/-2")
        self.assertEqual(rows["excluded"]["REMOTE"], "detached")
        self.assertEqual(rows["unknown"]["REMOTE"], "no-upstream")
        self.assertEqual(rows["integrated"]["HERDR"], "w7,w8")
        self.assertEqual(rows["recent"]["HERDR"], "-")
        self.assertEqual(rows["integrated"]["MARKER"], "🤖")
        self.assertEqual(rows["open"]["MARKER"], "💬")
        self.assertEqual(rows["unknown"]["MARKER"], "-")

    def test_failed_sources_hold_unknown(self):
        for failure in ("gh", "gh-malformed", "status", "ancestry"):
            with self.subTest(failure=failure):
                rows, _ = self.run_audit(failure=failure)
                self.assertEqual(rows["excluded"]["BUCKET"], "hold-unknown")
                column = "PR" if failure.startswith("gh") else "DIRTY" if failure == "status" else "MERGED"
                self.assertEqual(rows["excluded"][column], "unknown")

    def test_unavailable_herdr_is_not_closed(self):
        for state in ("failed", "outside"):
            with self.subTest(state=state):
                rows, _ = self.run_audit(herdr=state)
                self.assertTrue(all(row["HERDR"] == "unknown" for row in rows.values()))

    def test_candidates_preserve_usage_gates_and_content_integration(self):
        rows, _ = self.run_audit()
        self.assertEqual(rows["integrated"]["MERGED"], "no")
        for name, row in rows.items():
            self.assertEqual(row["PRUNE"], "-" if name == "excluded" else "candidate")

    def test_empty_preview_is_not_an_error(self):
        rows, stderr = self.run_audit("empty")
        self.assertTrue(all(row["PRUNE"] == "-" for row in rows.values()))
        self.assertNotIn("Prune preview unavailable", stderr)

    def test_failed_or_invalid_preview_is_unknown(self):
        for preview in ("failed", "malformed", "wrong-schema"):
            with self.subTest(preview=preview):
                rows, stderr = self.run_audit(preview)
                self.assertTrue(all(row["PRUNE"] == "unknown" for row in rows.values()))
                self.assertIn("Prune preview unavailable", stderr)


if __name__ == "__main__":
    unittest.main()
