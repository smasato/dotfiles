"""PR identity regressions: no network or worktree mutations."""
import importlib.util
from pathlib import Path
import unittest
from unittest import mock
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "worktrunk_prs", ROOT / "dot_config/worktrunk/prs.py")
prs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prs)


def pull(number=7, owner="example", branch="topic", sha="current", state="OPEN"):
    return dict(number=number, state=state, headRefName=branch, headRefOid=sha,
                headRepository=dict(name="repo"), headRepositoryOwner=dict(login=owner),
                url=f"https://github.com/example/repo/pull/{number}")


class PrTests(unittest.TestCase):
    def setUp(self):
        self.item = dict(branch="local-topic", upstream=dict(remote="origin", branch="topic"),
                         head=dict(sha="current"))
        self.repository = ("github.com", "example", "repo")

    def classify(self, candidates):
        return prs.classify(self.item, candidates, self.repository)

    def test_remote_url_forms(self):
        for value in ("git@github.com:Example/Repo.git", "https://github.com/Example/Repo.git",
                      "ssh://git@github.com/Example/Repo.git"):
            self.assertEqual(prs.repository_url(value), self.repository)
        for value in ("/tmp/repo", "../repo", "file:///tmp/repo", "https://github.com/a/b/c"):
            self.assertIsNone(prs.repository_url(value))

    def test_upstream_name_matches_local_alias(self):
        self.assertEqual(self.classify([pull()]), "#7/OPEN")

    def test_fork_with_same_branch_is_excluded(self):
        self.assertEqual(self.classify([pull(owner="other")]), "-")
        self.assertEqual(self.classify([pull(owner="other"), pull(8)]), "#8/OPEN")

    def test_reused_and_unpushed_heads_remain_unknown(self):
        for state in ("OPEN", "CLOSED", "MERGED"):
            self.assertEqual(self.classify([pull(sha="old", state=state)]), "unknown")

    def test_exact_merged_head_is_reported(self):
        self.assertEqual(self.classify([pull(state="MERGED")]), "#7/MERGED")

    def test_new_open_pr_does_not_fall_back_to_historical_merge(self):
        self.assertEqual(self.classify([pull(state="MERGED"), pull(8, sha="new")]), "unknown")
        self.assertEqual(self.classify([pull(sha="old", state="MERGED"), pull(8)]), "#8/OPEN")

    def test_ambiguous_prs_and_deleted_forks_are_unknown(self):
        self.assertEqual(self.classify([pull(), pull(8)]), "unknown")
        deleted = pull()
        deleted["headRepository"] = None
        self.assertEqual(self.classify([deleted]), "unknown")

    def test_truncated_list_cannot_prove_absence(self):
        candidates = [pull(number=i, branch="other") for i in range(1000)]
        self.assertEqual(self.classify(candidates), "unknown")
        self.assertEqual(self.classify(candidates[:999]), "-")

    def test_unknown_remote_and_no_upstream_are_held(self):
        self.assertEqual(prs.classify(self.item, [pull()], None), "unknown")
        self.item["upstream"] = None
        self.assertEqual(self.classify([]), "unknown")


class AnnotationMappingTests(unittest.TestCase):
    def setUp(self):
        self.repository = ("github.com", "example", "repo")
        self.items = [
            dict(branch="topic", head=dict(sha="current"),
                 upstream=dict(remote="origin", branch="topic"),
                 worktree=dict(path="/repo/topic")),
            dict(branch="orphan", head=dict(sha="current"),
                 upstream=dict(remote="origin", branch="topic")),
            dict(branch=None, head=dict(sha="detached"), upstream=None,
                 worktree=dict(path="/repo/detached", detached=True)),
        ]

    def lookup(self, pulls):
        return mock.patch.object(
            prs, "_lookup", return_value=(pulls, {"origin": self.repository, None: None}))

    def test_branch_annotations_cover_branch_only_items(self):
        with self.lookup([pull(state="MERGED")]):
            result = prs.branch_annotations(self.items)
        self.assertEqual(result, {"topic": "#7/MERGED", "orphan": "#7/MERGED"})

    def test_branch_annotations_omit_detached_and_hold_unknown(self):
        with self.lookup([pull(sha="old", state="MERGED")]):
            result = prs.branch_annotations(self.items)
        self.assertNotIn(None, result)
        self.assertEqual(result, {"topic": "unknown", "orphan": "unknown"})

    def test_annotations_stay_path_keyed_and_keep_detached(self):
        with self.lookup([pull(state="MERGED")]):
            result = prs.annotations(self.items)
        self.assertEqual(result, {
            "/repo/topic": "#7/MERGED",
            "/repo/detached": "unknown",
        })

    def test_lookup_failure_holds_everything_unknown(self):
        with mock.patch.object(prs, "_lookup", return_value=None):
            self.assertEqual(prs.branch_annotations(self.items),
                             {"topic": "unknown", "orphan": "unknown"})
            self.assertEqual(prs.annotations(self.items), {
                "/repo/topic": "unknown",
                "/repo/detached": "unknown",
            })


if __name__ == "__main__":
    unittest.main()
