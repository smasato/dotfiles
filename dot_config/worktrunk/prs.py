"""Read-only PR annotations. Ambiguous matches stay unknown.

annotations(items) keys results by checkout path for the audit table.
branch_annotations(items) keys results by branch and also covers
branch-only items without a worktree, for prune decisions.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit


FIELDS = "number,state,headRefName,headRefOid,headRepository,headRepositoryOwner,url"


def repository_url(value):
    """Normalize HTTPS, ssh:// and scp-style Git URLs; reject local/alias guesses."""
    if "://" not in value:
        match = re.fullmatch(r"[^/@:]+@([^/:]+):(.+)", value)
        if not match:
            return None
        value = f"ssh://{match[1]}/{match[2]}"
    parsed = urlsplit(value)
    if parsed.scheme not in ("https", "http", "ssh") or not parsed.hostname:
        return None
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return (parsed.hostname.lower(), *(part.lower() for part in parts))


def head_repository(pr):
    owner = (pr.get("headRepositoryOwner") or {}).get("login")
    name = (pr.get("headRepository") or {}).get("name")
    host = urlsplit(pr.get("url", "")).hostname
    if not all(isinstance(value, str) and value for value in (host, owner, name)):
        return None
    return host.lower(), owner.lower(), name.lower()


def classify(item, prs, repository):
    upstream = item.get("upstream") or {}
    branch = upstream.get("branch")
    sha = (item.get("head") or {}).get("sha")
    if not repository or not branch or not sha:
        return "unknown"
    named = [pr for pr in prs if pr["headRefName"] == branch]
    # Deleted forks have no head repository. Their name alone cannot exclude them.
    if any(head_repository(pr) is None for pr in named):
        return "unknown"
    candidates = [pr for pr in named if head_repository(pr) == repository]
    if not candidates:
        return "-" if len(prs) < 1000 else "unknown"
    opened = [pr for pr in candidates if pr["state"] == "OPEN"]
    # A newer open PR wins over historical PRs, but an unpushed/reused HEAD is
    # still uncertain. SHA mismatch must never become "no PR" or "merged".
    candidates = opened or candidates
    matched = [pr for pr in candidates if pr.get("headRefOid") == sha]
    if len(matched) != 1 or (opened and len(opened) != 1):
        return "unknown"
    pr = matched[0]
    return f"#{pr['number']}/{pr['state']}"


def _lookup(items):
    """Fetch the PR snapshot and resolve each item's upstream remote.

    Returns (prs, remotes) or None on any lookup failure; callers then hold
    every item unknown instead of guessing.
    """
    try:
        repo_url = json.loads(subprocess.check_output(
            ["gh", "repo", "view", "--json", "url"], text=True,
            stderr=subprocess.DEVNULL, timeout=30))["url"]
        repo = repository_url(repo_url)
        if not repo:
            raise ValueError("Unknown GitHub repository")
        prs = json.loads(subprocess.check_output(
            ["gh", "pr", "list", "--repo", repo_url, "--state", "all", "--limit", "1000", "--json", FIELDS],
            text=True, stderr=subprocess.DEVNULL, timeout=60))
        if not isinstance(prs, list) or not all(
            isinstance(pr, dict) and isinstance(pr.get("headRefName"), str)
            and pr.get("state") in ("OPEN", "CLOSED", "MERGED")
            and isinstance(pr.get("number"), int) for pr in prs
        ):
            raise ValueError("Invalid PR list")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"PR lookup unavailable: {error}", file=sys.stderr)
        return None
    remotes = {}
    for item in items:
        remote = (item.get("upstream") or {}).get("remote")
        if remote not in remotes:
            remotes[remote] = None
            if remote and remote != ".":
                try:
                    url = subprocess.check_output(
                        ["git", "remote", "get-url", "--", remote], text=True,
                        stderr=subprocess.DEVNULL, timeout=10).strip()
                    remotes[remote] = repository_url(url)
                    # SSH aliases and another forge/host cannot be matched to
                    # this PR snapshot by guessing their canonical hostname.
                    if remotes[remote] and remotes[remote][0] != repo[0]:
                        remotes[remote] = None
                except (OSError, ValueError, subprocess.SubprocessError):
                    pass
    return prs, remotes


def _classifications(items):
    """Classify every item once; shared by both annotation mappings."""
    lookup = _lookup(items)
    if lookup is None:
        return ["unknown"] * len(items)
    prs, remotes = lookup
    return [
        classify(item, prs, remotes.get((item.get("upstream") or {}).get("remote")))
        for item in items
    ]


def annotations(items):
    """Map checkout path to PR state for items that have a worktree."""
    states = _classifications(items)
    return {
        item["worktree"]["path"]: state
        for item, state in zip(items, states) if item.get("worktree")
    }


def branch_annotations(items):
    """Map branch name to PR state, including branch-only items.

    Detached worktrees and items without a branch are omitted; callers treat
    a missing key as unknown.
    """
    states = _classifications(items)
    return {
        item["branch"]: state
        for item, state in zip(items, states) if item.get("branch")
    }


if __name__ == "__main__":
    items = json.loads(Path(sys.argv[1]).read_text())["items"]
    print(json.dumps(annotations(items)))
