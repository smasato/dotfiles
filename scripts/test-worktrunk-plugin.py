"""Render the chezmoi updater and test its CLI contract without network writes."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PluginTests(unittest.TestCase):
    def test_installed_fresh_and_offline(self):
        rendered = subprocess.check_output([
            "chezmoi", "execute-template", "--file",
            str(ROOT / ".chezmoiscripts/run_after_04-claude-worktrunk.sh.tmpl")], text=True)
        subprocess.run(["shellcheck", "-"], input=rendered, text=True, check=True)
        for mode in ("installed", "fresh", "offline", "missing-after-install", "disabled"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                log = root / "calls"
                mise = root / "mise"
                mise.write_text("#!/bin/sh\nexit 0\n")
                mise.chmod(0o755)
                claude = root / "claude"
                claude.write_text(f"#!{sys.executable}\n" + '''import json,os,pathlib,sys
assert 'CLAUDE_CONFIG_DIR' not in os.environ
args=sys.argv[1:]
with open(os.environ['LOG'],'a') as f: f.write(json.dumps(args)+'\\n')
mode=os.environ['MODE']
installed=pathlib.Path(os.environ['HOME'])/'installed'
if mode=='offline': sys.exit(1)
if args==['plugin','marketplace','list','--json']:
 print(json.dumps([{'name':'worktrunk'}] if mode=='installed' else []))
elif args==['plugin','list','--json']:
 print(json.dumps([{'id':'worktrunk@worktrunk','scope':'user','enabled':mode!='disabled'}]
                  if mode=='installed' or installed.exists() else []))
elif args[:2]==['plugin','install'] and mode!='missing-after-install': installed.touch()
''')
                claude.chmod(0o755)
                # Only replace the production PATH boundary; keep the rendered body intact.
                script = rendered.replace(
                    'export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"',
                    'export PATH=' + shlex.quote(f"{root}:{os.environ['PATH']}"))
                result = subprocess.run(["/bin/bash"], input=script, text=True,
                                        env=dict(os.environ, HOME=str(root), MODE=mode,
                                                 LOG=str(log), CLAUDE_CONFIG_DIR="work-home"))
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                if mode == "offline":
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(len(calls), 1)
                elif mode in ("missing-after-install", "disabled"):
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(calls[-1], ["plugin", "list", "--json"])
                else:
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(calls, [
                        ["plugin", "marketplace", "list", "--json"],
                        ["plugin", "marketplace", "update", "worktrunk"] if mode == "installed"
                        else ["plugin", "marketplace", "add", "max-sixty/worktrunk"],
                        ["plugin", "list", "--json"],
                        ["plugin", "update" if mode == "installed" else "install",
                         "worktrunk@worktrunk", "--scope", "user"],
                        ["plugin", "list", "--json"],
                    ])


if __name__ == "__main__":
    unittest.main()
