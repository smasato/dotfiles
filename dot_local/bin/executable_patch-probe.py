#!/usr/bin/env python3
"""Repair Probe rc339's missing native grep command using ripgrep.

Remove this hook when upgrading to a release with a working grep implementation.
Both the SDK and MCP build copy need the same fix. Refuse unexpected sources.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


install = os.environ.get("MISE_TOOL_INSTALL_PATH")
if not install:
    install = subprocess.check_output(
        ["mise", "where", "npm:@probelabs/probe"], text=True
    ).strip()
package = Path(install) / "lib/node_modules/@probelabs/probe"
version = json.loads((package / "package.json").read_text())["version"]
if version != "0.6.0-rc339":
    raise SystemExit(f"Review Probe grep repair before upgrading from rc339: {version}")
if not shutil.which("rg"):
    raise SystemExit("Probe grep repair requires mise-managed ripgrep on PATH")

replacements = {
    "import { getBinaryPath, getCleanEnv }": "import { getCleanEnv }",
    "filesWithoutMatches: '-L'": "filesWithoutMatches: '--files-without-match'",
    "noGitignore: '--no-gitignore'": "noGitignore: '--no-ignore-vcs'",
    "const binaryPath = await getBinaryPath(options.binaryOptions || {});":
        "const binaryPath = 'rg';",
    "const cliArgs = ['grep'];": "const cliArgs = [];",
    "cliArgs.push(options.pattern);": "cliArgs.push('--', options.pattern);",
}
pending = []
for relative in ("src/grep.js", "build/grep.js"):
    path = package / relative
    source = path.read_text()
    if all(new in source and old not in source for old, new in replacements.items()):
        continue
    if hashlib.sha256(source.encode()).hexdigest() != "3086ea0d8e92b1359538543e3a4f9750451bbf3a0a14ab475a3a837b33c78553":
        raise SystemExit(f"Unexpected Probe source; refusing to patch {path}")
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise SystemExit(f"Unexpected Probe source: {relative}: {old}")
        source = source.replace(old, new)
    pending.append((path, source))
for path, source in pending:
    path.write_text(source)
print(f"Probe grep repair ready ({len(pending)} files patched)")
