"""Run every check that CI runs: Markdown lint, links, file names, sizes, READMEs, and the script tests.

Run from the repository root: python scripts/check.py
Needs Node.js (for npx) and Python 3. Exits non-zero if any check fails.
"""
import os
import shutil
import subprocess
import sys

MARKDOWNLINT = "markdownlint-cli2@0.23.3"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

steps = [
    ("Markdown lint", f'npx --yes {MARKDOWNLINT} "**/*.md"', True),
    ("Links, file names, sizes, and READMEs", [sys.executable, os.path.join(HERE, "check_docs.py")], False),
    ("Script tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"], False),
]

failed = []
for name, cmd, shell in steps:
    print(f"\n== {name}", flush=True)
    if shell and not shutil.which("npx"):
        print("npx not found. Install Node.js 22 (see .nvmrc), then run this again.")
        failed.append(name)
        continue
    if subprocess.run(cmd, cwd=ROOT, shell=shell).returncode != 0:
        failed.append(name)

print("\n" + ("All checks passed." if not failed else "Failed: " + ", ".join(failed)))
sys.exit(1 if failed else 0)
