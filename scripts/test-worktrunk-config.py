"""The shared gate must reject list settings that hook dry-runs accept."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def test_invalid_columns_fail_before_other_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", "--initial-branch=main", str(root)], check=True)
            config = root / "dot_config/worktrunk/config.toml"
            config.parent.mkdir(parents=True)
            config.write_text('[list]\ncolumns = ["not-a-real-column"]\n')
            checker = root / "scripts/check-worktrunk.py"
            checker.parent.mkdir()
            checker.write_bytes((ROOT / "scripts/check-worktrunk.py").read_bytes())
            result = subprocess.run([sys.executable, str(checker)], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("config', 'show'", result.stderr)
            self.assertNotIn("No Worktrunk tests found", result.stderr)


if __name__ == "__main__":
    unittest.main()
