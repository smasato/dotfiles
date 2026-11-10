"""Verify OMP quota guards survive existing per-profile settings."""

from pathlib import Path
import json
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = {
    "default": "dot_omp/private_agent/modify_private_config.yml",
    "experimental": "dot_omp/private_profiles/experimental/private_agent/modify_private_config.yml",
    "security": "dot_omp/private_profiles/security/private_agent/modify_private_config.yml",
}
# The default profile enforces its fallback chains; the others keep existing ones.
ENFORCED_DEFAULT_CHAIN = {"default": ["anthropic/claude-opus-5-5:high"]}


def render(template, current, home):
    wrapper = (
        '{{- $context := deepCopy . -}}'
        '{{- $_ := set $context.chezmoi "homeDir" ' + json.dumps(str(home)) + ' -}}'
        '{{ includeTemplate ' + json.dumps(template) + ' $context | fromYaml | toJson }}'
    )
    result = subprocess.run(
        ["chezmoi", "--source", str(ROOT), "execute-template", "--with-stdin", wrapper],
        input=json.dumps(current),
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    return json.loads(result.stdout)


class OmpQuotaPolicyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.current = {
            "modelRoles": {
                "default": "openai-codex/gpt-6-luna:medium",
                "task": "anthropic/claude-haiku-5-5:low",
            },
            "retry": {
                "usageAwareFallback": False,
                "usageReservePct": 0,
                "usageReservePolicy": "auto",
                "maxRetries": 2,
                "modelFallback": False,
                "fallbackChains": {"default": ["openai-codex/gpt-6-luna"]},
            },
            "codexResets": {"autoRedeem": "yes", "keepCredits": 2},
        }
        base = self.home / ".omp" / "agent" / "config.yml"
        base.parent.mkdir(parents=True)
        base.write_text(json.dumps(self.current))

    def test_existing_values_cannot_disable_quota_guards(self):
        for profile, template in TEMPLATES.items():
            with self.subTest(profile=profile):
                config = render(template, self.current, self.home)
                self.assertTrue(config["retry"]["usageAwareFallback"])
                self.assertEqual(config["retry"]["usageReservePct"], 10)
                self.assertEqual(config["retry"]["usageReservePolicy"], "fail-closed")
                self.assertEqual(config["codexResets"]["autoRedeem"], "no")

    def test_quota_guards_preserve_model_routing_and_retry_choices(self):
        for profile, template in TEMPLATES.items():
            with self.subTest(profile=profile):
                config = render(template, self.current, self.home)
                for role, model in self.current["modelRoles"].items():
                    self.assertEqual(config["modelRoles"][role], model)
                for key in ("maxRetries", "modelFallback"):
                    self.assertEqual(config["retry"][key], self.current["retry"][key])
                self.assertEqual(
                    config["retry"]["fallbackChains"]["default"],
                    ENFORCED_DEFAULT_CHAIN.get(
                        profile, self.current["retry"]["fallbackChains"]["default"]
                    ),
                )
                self.assertEqual(config["codexResets"]["keepCredits"], 2)
                self.assertEqual(render(template, config, self.home), config)


if __name__ == "__main__":
    unittest.main()
