#!/usr/bin/env python3
"""Exercise ownership migration and deployment staging without touching live settings."""

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "dot_agents/skills/pstack-runtime"


class SkillValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("check_pstack", ROOT / "scripts/check-pstack.py")
        cls.checker = importlib.util.module_from_spec(spec)
        with patch("sys.dont_write_bytecode", True):
            spec.loader.exec_module(cls.checker)

    def validate(self, resources):
        with tempfile.TemporaryDirectory(prefix="skill-contract-test-") as directory:
            skills = Path(directory)
            for relative, content in resources.items():
                target = skills / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            names = sorted({relative.split("/")[0] for relative in resources})
            with patch.object(self.checker, "SKILLS", skills), patch.object(self.checker, "NAMES", names):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.checker.check()

    def test_standalone_skill_does_not_require_runtime(self):
        self.validate({"plain/SKILL.md": "---\nname: plain\ndescription: Plain writing.\n---\n\nWrite clearly.\n"})

    def test_optional_runtime_link_is_validated(self):
        self.validate({
            "plain/SKILL.md": "---\nname: plain\ndescription: Scoped work.\n---\n\nFor delegation, read [runtime](../pstack-runtime/SKILL.md).\n",
            "pstack-runtime/SKILL.md": "---\nname: pstack-runtime\ndescription: Execution contract.\n---\n",
        })

    def test_missing_reference_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "missing link"):
            self.validate({"plain/SKILL.md": "---\nname: plain\ndescription: Scoped work.\n---\n\nRead [missing](references/missing.md).\n"})

    def test_legacy_unconditional_runtime_preamble_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "unported host dependency"):
            self.validate({"plain/SKILL.md": "---\nname: plain\ndescription: Plain writing.\n---\n\nRead runtime before executing this workflow. It defines native delegation, model roles, history, and monitoring for Claude Code and Codex.\n"})

    def test_explicit_invocation_still_requires_host_policy(self):
        entry = "---\nname: plain\ndescription: Explicit writing.\ndisable-model-invocation: true\n---\n"
        with self.assertRaisesRegex(SystemExit, "explicit-invocation policy missing"):
            self.validate({"plain/SKILL.md": entry})
        self.validate({"plain/SKILL.md": entry, "plain/agents/openai.yaml": "policy:\n  allow_implicit_invocation: false\n"})

    def test_unported_tool_arguments_are_rejected(self):
        with self.assertRaisesRegex(SystemExit, "unported host dependency"):
            self.validate({"plain/SKILL.md": "---\nname: plain\ndescription: Scoped work.\n---\n\nSpawn with cloud_base_branch.\n"})


class PortTests(unittest.TestCase):
    def test_cli_ownership_is_scoped_recoverable_and_idempotent(self):
        original = {
            "version": 3,
            "skills": {
                "Poteto Mode": {"source": "cursor/plugins", "skillPath": "pstack/skills/poteto-mode/SKILL.md"},
                "tdd": {"source": "my/fork", "skillPath": "pstack/skills/tdd/SKILL.md"},
                "swarm": {"source": "cursor/plugins", "skillPath": "another/swarm/SKILL.md"},
                "unrelated": {"source": "elsewhere/tools"},
            },
        }
        with tempfile.TemporaryDirectory(prefix="pstack-lock-test-") as directory:
            lock = Path(directory) / "lock.json"
            lock.write_text(json.dumps(original))
            command = ["node", str(RUNTIME / "scripts/detach-cli-lock.mjs"), str(lock)]
            subprocess.run(command, check=True, capture_output=True)
            migrated = json.loads(lock.read_text())
            self.assertEqual(set(migrated["skills"]), {"tdd", "swarm", "unrelated"})
            self.assertEqual(migrated["version"], 3)
            backup = Path(str(lock) + ".before-pstack-port")
            self.assertEqual(json.loads(backup.read_text()), original)
            before = lock.stat().st_mtime_ns
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(lock.stat().st_mtime_ns, before)
            self.assertEqual(json.loads(backup.read_text()), original)

    def test_deployment_layout_preserves_resources_and_executables(self):
        with tempfile.TemporaryDirectory(prefix="pstack-layout-test-") as directory:
            subprocess.run(["python3", str(ROOT / "scripts/check-pstack.py"), "--stage", directory], check=True, capture_output=True)
            stage = Path(directory)
            watcher = stage / "poteto-mode/scripts/watch-pr/watch-pr"
            self.assertTrue(watcher.stat().st_mode & 0o111)
            self.assertTrue((stage / "no-comments/references/comment-sicko.md").is_file())
            self.assertTrue((stage / "poteto-mode/agents/openai.yaml").is_file())
            self.assertFalse(list(stage.rglob("executable_*")))
            original = ROOT / "dot_agents/skills/poteto-mode/scripts/watch-pr/executable_watch-pr"
            self.assertEqual(watcher.read_bytes(), original.read_bytes())


if __name__ == "__main__":
    unittest.main()
