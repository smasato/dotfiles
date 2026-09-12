"""Validate Worktrunk settings and include the Herdr picker in the shared gate."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PICKER_CONFIG = Path("dot_config/herdr/plugins/config/worktrunk/config.toml")


class ConfigTests(unittest.TestCase):
    def test_picker_config_values(self):
        with (ROOT / PICKER_CONFIG).open("rb") as file:
            config = tomllib.load(file)
        # Check the managed keys, without pinning the current placement or size.
        self.assertEqual(set(config), {
            "show_remote_branches", "picker_placement", "popup_width", "popup_height",
        })
        self.assertIs(type(config["show_remote_branches"]), bool)
        self.assertIn(config["picker_placement"], ("split", "popup"))
        for key in ("popup_width", "popup_height"):
            with self.subTest(key=key):
                value = config[key]
                self.assertIn(type(value), (int, str))
                dimension = str(value)
                self.assertRegex(dimension, r"\A[0-9]+%?\Z")
                self.assertGreater(int(dimension.removesuffix("%")), 0)
                if dimension.endswith("%"):
                    self.assertLessEqual(int(dimension[:-1]), 100)

    def test_hk_checks_picker_config(self):
        result = subprocess.run(
            ["hk", "check", "--plan", "--json", str(PICKER_CONFIG)],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        plan = json.loads(result.stdout)
        step = next(step for step in plan["steps"] if step["name"] == "worktrunk")
        self.assertNotEqual(step["status"], "skipped", step)
        self.assertEqual(step["fileCount"], 1)

    def test_invalid_columns_fail_before_other_checks(self):
        # Commit hooks export Git paths that must not affect this fixture repo.
        local_vars = subprocess.check_output(
            ["git", "rev-parse", "--local-env-vars"], text=True).splitlines()
        env = {key: value for key, value in os.environ.items() if key not in local_vars}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", "--initial-branch=main", str(root)], check=True, env=env)
            config = root / "dot_config/worktrunk/config.toml"
            config.parent.mkdir(parents=True)
            config.write_text('[list]\ncolumns = ["not-a-real-column"]\n')
            checker = root / "scripts/check-worktrunk.py"
            checker.parent.mkdir()
            checker.write_bytes((ROOT / "scripts/check-worktrunk.py").read_bytes())
            result = subprocess.run([sys.executable, str(checker)], text=True, capture_output=True, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("config', 'show'", result.stderr)
            self.assertNotIn("No Worktrunk tests found", result.stderr)


if __name__ == "__main__":
    unittest.main()
