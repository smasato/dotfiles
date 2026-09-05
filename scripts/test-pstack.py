#!/usr/bin/env python3
"""Exercise ownership migration and deployment staging without touching live settings."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "dot_agents/skills/pstack-runtime"


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
