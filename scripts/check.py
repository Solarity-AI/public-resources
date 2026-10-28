"""Run every check that CI runs: Markdown lint, links, file names, sizes, READMEs, and the script tests.

Run from the repository root: python scripts/check.py
Needs Python 3 and Node.js 22, with `npm ci` run once to install markdownlint-cli2 from package-lock.json.
Exits non-zero if any check fails.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

if len(sys.argv) > 1:  # no options: -h, --help, or anything else prints this
    print(__doc__)
    sys.exit(0 if sys.argv[1] in ("-h", "--help") else 2)


def lint_install_matches_lockfile():
    """npm ci records what it installed in node_modules/.package-lock.json; after a pull that changes
    package-lock.json, the two differ until npm ci runs again."""
    try:
        with open(os.path.join(ROOT, "package-lock.json"), encoding="utf-8") as f:
            locked = json.load(f)["packages"]
        with open(os.path.join(ROOT, "node_modules", ".package-lock.json"), encoding="utf-8") as f:
            installed = json.load(f)["packages"]
    except (OSError, ValueError, KeyError):
        return False
    return all(installed.get(path, {}).get("version") == info.get("version")
               for path, info in locked.items() if path and not info.get("optional"))


steps = [
    # --no: use the locked install in node_modules, never download a different version
    ("Markdown lint", 'npx --no markdownlint-cli2 "**/*.md"', True),
    ("Links, file names, sizes, and READMEs", [sys.executable, os.path.join(HERE, "check_docs.py")], False),
    ("Script tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"], False),
]

failed = []
for name, cmd, shell in steps:
    print(f"\n== {name}", flush=True)
    if shell and not shutil.which("npx"):
        print("npx not found. Install Node.js 22 (see .nvmrc), run npm ci, then run this again.")
        failed.append(name)
        continue
    if shell and not os.path.isdir(os.path.join(ROOT, "node_modules", "markdownlint-cli2")):
        print("markdownlint-cli2 isn't installed. Run npm ci (it installs the version in package-lock.json), then run this again.")
        failed.append(name)
        continue
    if shell and not lint_install_matches_lockfile():
        print("The linter in node_modules doesn't match package-lock.json. Run npm ci again, then run this again.")
        failed.append(name)
        continue
    if subprocess.run(cmd, cwd=ROOT, shell=shell).returncode != 0:
        failed.append(name)

print("\n" + ("All checks passed." if not failed else "Failed: " + ", ".join(failed)))
sys.exit(1 if failed else 0)
