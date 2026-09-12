"""Local Worktrunk checks. Creation uses temporary repos; Herdr/forge calls use stubs."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
subprocess.run(["wt", "--config", str(ROOT / "dot_config/worktrunk/config.toml"),
                "config", "show"], check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
scripts = sorted(ROOT.glob("dot_config/herdr/scripts/*worktree*.sh"))
scripts.extend(ROOT / path for path in (
    "dot_config/herdr/scripts/executable_lazygit-tab.sh",
    "dot_config/herdr/scripts/executable_update-plugins.sh",
    "dot_local/bin/executable_herdr-worktrees",
))
scripts.append(ROOT / "dot_agents/skills/poteto-mode/scripts/executable_worktree-audit.sh")
subprocess.run(["shellcheck", *map(str, scripts)], check=True)
suite = unittest.TestSuite()
for pattern in ("test-worktrunk*.py", "test-worktree-audit.py", "test-codex-config.py"):
    for path in sorted((ROOT / "scripts").glob(pattern)):
        spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
assert suite.countTestCases(), "No Worktrunk tests found"
sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
