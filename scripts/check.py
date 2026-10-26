"""Run every check that CI runs: Markdown lint, then links, file names, sizes, and READMEs.

Run from the repository root: python scripts/check.py
Needs Node.js (for npx) and Python 3. Exits non-zero if any check fails.
"""
import os
import subprocess
import sys

MARKDOWNLINT = "markdownlint-cli2@0.18.1"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

steps = [
    ("Markdown lint", f'npx --yes {MARKDOWNLINT} "**/*.md"', True),
    ("Links, file names, sizes, and READMEs", [sys.executable, os.path.join(HERE, "check_docs.py")], False),
]

failed = []
for name, cmd, shell in steps:
    print(f"\n== {name}", flush=True)
    if subprocess.run(cmd, cwd=ROOT, shell=shell).returncode != 0:
        failed.append(name)

print("\n" + ("All checks passed." if not failed else "Failed: " + ", ".join(failed)))
sys.exit(1 if failed else 0)
