"""Verify Codex defaults preserve existing per-home settings."""

from pathlib import Path
import subprocess
import tomllib
import unittest


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "dot_codex/modify_private_config.toml"


def render(current):
    return subprocess.run(
        ["chezmoi", "execute-template", "--with-stdin", "--file", str(TEMPLATE)],
        input=current,
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    ).stdout


class CodexConfigTests(unittest.TestCase):
    def test_new_home_gets_defaults(self):
        config = tomllib.loads(render(""))
        self.assertEqual(config["model"], "gpt-6-astra")
        self.assertEqual(config["model_reasoning_effort"], "medium")
        self.assertTrue(config["features"]["hooks"])
        self.assertTrue(config["plugins"]["worktrunk@worktrunk"]["enabled"])
        self.assertEqual(config["marketplaces"]["worktrunk"]["source_type"], "git")
        self.assertEqual(config["projects"][str(ROOT)]["trust_level"], "trusted")

    def test_existing_settings_take_precedence(self):
        current = '''
model = "custom-model"
model_reasoning_effort = "low"
service_tier = "default"
custom_empty = ""
custom_zero = 0
custom_array = []
[features]
hooks = false
[mcp_servers.linear]
url = "https://mcp.linear.app/mcp"
[mcp_servers.computer-use]
args = []
[plugins."sites@openai-bundled"]
enabled = false
[plugins."worktrunk@worktrunk"]
enabled = false
[marketplaces.worktrunk]
source_type = "local"
source = "/custom/marketplace"
[hooks.state.example]
trusted = false
[tui.model_availability_nux]
"gpt-5.6-sol" = 0
'''
        current += f'\n[projects."{ROOT}"]\ntrust_level = "untrusted"\n'
        result = tomllib.loads(render(current))

        def assert_preserved(expected, actual):
            for key, value in expected.items():
                if isinstance(value, dict):
                    assert_preserved(value, actual[key])
                else:
                    self.assertEqual(actual[key], value, key)

        assert_preserved(tomllib.loads(current), result)
        self.assertIn("openaiDeveloperDocs", result["mcp_servers"])

    def test_apply_is_idempotent(self):
        first = render('model_reasoning_effort = "low"\n')
        self.assertEqual(render(first), first)

    def test_complete_config_preserves_comments_and_formatting(self):
        current = "# Keep this comment.\n" + render("")
        self.assertEqual(render(current), current)

    def test_home_templates_are_identical(self):
        for seat in (1, 2, 3):
            self.assertEqual(
                (ROOT / f"dot_codex_work{seat}/modify_private_config.toml").read_bytes(),
                TEMPLATE.read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
