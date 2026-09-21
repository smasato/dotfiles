"""Prune integrated branches only after branch-local work and a safe PR check."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
import prs


def output(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE).strip()


def creation_commit(branch):
    """Require an intact creation record, not merely the oldest surviving commit."""
    path = output("git", "rev-parse", "--path-format=absolute", "--git-path",
                  f"logs/refs/heads/{branch}")
    with Path(path).open() as log:
        first = log.readline()
        fields, separator, message = first.partition("\t")
        hashes = fields.split()[:2]
        if (not separator or len(hashes) != 2 or set(hashes[0]) != {"0"}
                or not message.startswith("branch: Created from ")):
            return None
        created = hashes[1]
        # A copied branch inherits its source's reflog. Its own starting point is
        # the copy, not the source branch's original creation commit.
        for line in log:
            fields, _, message = line.partition("\t")
            if message.startswith("Branch: copied "):
                created = fields.split()[1]
    return created if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", created) else None


def has_branch_changes(branch, head):
    created = creation_commit(branch)
    if not created or created == head:
        return False
    return output("git", "rev-parse", f"{created}^{{tree}}") != output(
        "git", "rev-parse", f"{head}^{{tree}}")


def same_checkout(candidate, item):
    if candidate.get("kind") == "branch_only":
        return not item.get("worktree") and candidate.get("path") is None
    worktree = item.get("worktree") or {}
    return (candidate.get("kind") in ("worktree", "current")
            and candidate.get("path") == worktree.get("path")
            and not worktree.get("main") and not worktree.get("locked")
            and not worktree.get("prunable") and not worktree.get("detached")
            and not worktree.get("operation"))


def held(branch, reason):
    print(f"Keep {branch}: {reason}", file=sys.stderr)


def plan(wt):
    inventory = json.loads(output(*wt, "list", "--branches", "--format=json"))
    if inventory.get("schema") != 2 or not isinstance(inventory.get("items"), list):
        raise ValueError("Invalid wt list snapshot")
    items = inventory["items"]
    default = inventory.get("repo", {}).get("default_branch")
    if not default:
        raise ValueError("Default branch is unknown")
    candidates = json.loads(output(*wt, "step", "prune", "--dry-run", "--min-age=0s", "--format=json"))
    if not isinstance(candidates, list):
        raise ValueError("Invalid wt prune preview")
    eligible = []
    for candidate in candidates:
        branch = candidate.get("branch")
        if not branch or branch == default or candidate.get("branch_deleted") is not True:
            continue
        matches = [item for item in items if item.get("branch") == branch and not item.get("remote")]
        if len(matches) != 1 or not same_checkout(candidate, matches[0]):
            held(branch, "checkout identity is unknown")
            continue
        item = matches[0]
        head = (item.get("head") or {}).get("sha")
        try:
            if not head or output("git", "rev-parse", "--verify", f"refs/heads/{branch}") != head:
                held(branch, "HEAD changed during inspection")
                continue
            if not has_branch_changes(branch, head):
                held(branch, "no content changes since creation, or creation record unavailable")
                continue
        except (OSError, ValueError, IndexError, subprocess.SubprocessError):
            held(branch, "creation history is unavailable")
            continue
        eligible.append((candidate, item))
    if not eligible:
        return []
    # A repository without remotes has no forge identity to query. Configured
    # remotes must pass the shared identity check; lookup failure is not no-PR.
    states = (prs.branch_annotations([item for _, item in eligible])
              if output("git", "remote") else {candidate["branch"]: "-" for candidate, _ in eligible})
    approved = []
    for candidate, item in eligible:
        branch = candidate["branch"]
        state = states.get(branch, "unknown")
        if state != "-" and not re.fullmatch(r"#[0-9]+/MERGED", state):
            held(branch, f"PR {state}")
            continue
        approved.append(dict(candidate, head=item["head"]["sha"], pr=state,
                             current=bool((item.get("worktree") or {}).get("current"))))
    return sorted(approved, key=lambda candidate: candidate["current"])


def unchanged(candidate):
    branch = candidate["branch"]
    if output("git", "rev-parse", "--verify", f"refs/heads/{branch}") != candidate["head"]:
        return False
    path = candidate.get("path")
    if path:
        return (output("git", "-C", path, "symbolic-ref", "HEAD") == f"refs/heads/{branch}"
                and output("git", "-C", path, "rev-parse", "HEAD") == candidate["head"]
                and not output("git", "-C", path, "status", "--porcelain", "--untracked-files=all"))
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show approved candidates without deleting")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--config", help="Worktrunk user config")
    parser.add_argument("-C", dest="directory", default=".")
    parser.add_argument("--yes", "-y", action="store_true", help="approve removal hooks")
    parser.add_argument("--foreground", action="store_true", help="accepted for compatibility; removal always waits")
    args = parser.parse_args()
    os.chdir(args.directory)
    wt = ["wt"]
    if args.config:
        wt.extend(["--config", str(Path(args.config).resolve())])
    wt.extend(["--config-set", "list.json-schema=2", "--config-set", "list.full=false",
               "--config-set", "list.summary=false"])
    candidates = plan(wt)
    if args.dry_run:
        if args.format == "json":
            print(json.dumps(candidates, indent=2))
        else:
            for candidate in candidates:
                print(f"Would remove {candidate['branch']}: {candidate['reason']} {candidate['target']}; PR {candidate['pr']}")
            if not candidates:
                print("No eligible worktrees or branches.")
        return 0
    results = []
    for candidate in candidates:
        branch = candidate["branch"]
        # Recheck integration/lock/dirty state immediately before each removal.
        # wt remove also checks branch integration and never receives force flags.
        fresh = json.loads(output(*wt, "step", "prune", "--dry-run", "--min-age=0s", "--format=json"))
        if not any(row.get("branch") == branch and row.get("path") == candidate.get("path")
                   and row.get("branch_deleted") is True for row in fresh) or not unchanged(candidate):
            held(branch, "state changed before removal")
            continue
        command = [*wt, "remove", "--foreground", "--format=json"]
        if args.yes:
            command.append("--yes")
        result = subprocess.run([*command, "--", candidate.get("path") or branch],
                                text=True, stdout=subprocess.PIPE, check=True)
        results.extend(json.loads(result.stdout))
    if args.format == "json":
        print(json.dumps(results, indent=2))
    elif not candidates:
        print("No eligible worktrees or branches.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"wt-prune: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        sys.exit(1)
