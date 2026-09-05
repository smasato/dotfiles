#!/usr/bin/env python3
"""Validate the managed pstack port and optionally stage its deployed layout."""

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "dot_agents/skills"
MANIFEST = json.loads((SKILLS / "pstack-runtime/references/upstream.json").read_text())
NAMES = [entry["dir"] for entry in MANIFEST["skills"]] + ["pstack-runtime"]
FORBIDDEN = re.compile(
    r"\.cursor/|generalPurpose|cloud_base_branch|allow_multiple|claude-\S*-thinking|grok-4\.6|gpt-5\.6-sol-max|"
    r"git show origin/main:pstack|cloud-sleeper|readonly strips MCP|"
    r"\bCursor dashboard\b|\bcreate-skill\b|\bgt (?:submit|track|restack|sync)"
)


def deployed_name(path):
    return path.name.removeprefix("executable_")


def files():
    for name in NAMES:
        for source in (SKILLS / name).rglob("*"):
            if source.is_file():
                relative = source.relative_to(SKILLS)
                yield source, relative.with_name(deployed_name(source))


def check():
    errors = []
    contents = {str(relative): source.read_text() for source, relative in files()}
    for name in NAMES:
        entry = contents.get(f"{name}/SKILL.md", "")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", entry, re.S)
        if not frontmatter:
            errors.append(f"{name}: missing frontmatter")
            continue
        fields = frontmatter.group(1)
        if not re.search(rf"^name: {re.escape(name)}$", fields, re.M):
            errors.append(f"{name}: name does not match directory")
        if not re.search(r"^description: .+", fields, re.M):
            errors.append(f"{name}: missing description")
        if name != "pstack-runtime" and "../pstack-runtime/SKILL.md" not in entry:
            errors.append(f"{name}: missing native runtime routing")
        if "disable-model-invocation: true" in fields:
            policy = contents.get(f"{name}/agents/openai.yaml", "")
            if "allow_implicit_invocation: false" not in policy:
                errors.append(f"{name}: Codex explicit-invocation policy missing")
    for relative, body in contents.items():
        if "mise WARN" in body or "failed to write cache file" in body:
            errors.append(f"{relative}: captured command warning in resource")
        if relative.endswith((".md", ".ts", ".mjs", ".sh")):
            for number, line in enumerate(body.splitlines(), 1):
                if FORBIDDEN.search(line):
                    errors.append(f"{relative}:{number}: unported host dependency")
        if not relative.endswith(".md"):
            continue
        # Check concrete local Markdown links. Templates and external links are not files.
        for target in re.findall(r"\]\(([^)]+)\)", body):
            if target == "url" or re.match(r"[a-z]+:|#|/|~", target) or any(c in target for c in "<>*"):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = (SKILLS / relative).parent.joinpath(target).resolve()
            try:
                key = str(resolved.relative_to(SKILLS.resolve()))
            except ValueError:
                continue
            if key not in contents and not resolved.is_dir():
                errors.append(f"{relative}: missing link {target}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(NAMES)} skills, {len(contents)} resources; native paths, links, invocation policies")


def stage(directory):
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise SystemExit("staging directory must be empty")
    for source, relative in files():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if source.name.startswith("executable_"):
            target.chmod(0o755)
    print(f"Staged deployed skill layout: {directory}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path)
    args = parser.parse_args()
    check()
    if args.stage:
        stage(args.stage)
