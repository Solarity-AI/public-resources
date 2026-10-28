"""Tests for scripts/check.py and the Markdown lint setup it runs. Run: python -m unittest discover -s tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

# support.py sits beside this file; discover puts this folder on sys.path, and this covers tests.<module> runs too
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from support import GOOD_README, ROOT, copy_script, write


class CheckPyTest(unittest.TestCase):
    """scripts/check.py is the one command CI runs, so any failed step must fail the run (#107)."""

    def check(self, d, npx_exit=None, readme="", test_body="pass", installed="1.0.0"):
        copy_script(d, "check.py")
        copy_script(d, "check_docs.py")
        write(d, "brand/README.md", GOOD_README + readme)
        write(d, "package-lock.json", json.dumps({"packages": {"": {}, "node_modules/markdownlint-cli2": {"version": "1.0.0"}}}))
        if installed:  # what npm ci leaves behind, at the version it installed
            write(d, "node_modules/markdownlint-cli2/package.json", "{}")
            write(d, "node_modules/.package-lock.json",
                  json.dumps({"packages": {"node_modules/markdownlint-cli2": {"version": installed}}}))
        write(d, "tests/test_ok.py", f"import unittest\n\n\nclass T(unittest.TestCase):\n    def test_it(self):\n        {test_body}\n")
        bin_dir = os.path.join(d, "bin")
        os.makedirs(bin_dir)
        if npx_exit is not None:  # a stand-in for npx, so the test needs neither Node nor the network
            if os.name == "nt":
                write(bin_dir, "npx.cmd", f"@exit /b {npx_exit}\n")
            else:
                write(bin_dir, "npx", f"#!/bin/sh\nexit {npx_exit}\n")
                os.chmod(os.path.join(bin_dir, "npx"), 0o755)
        return subprocess.run([sys.executable, os.path.join(d, "scripts", "check.py")], cwd=d,
                              env=dict(os.environ, PATH=bin_dir), capture_output=True, text=True)

    def test_passes_when_every_step_passes(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.check(d, npx_exit=0)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("All checks passed.", r.stdout)

    def test_any_failed_step_fails_the_run(self):
        cases = {
            "Markdown lint": dict(npx_exit=1),
            "Links, file names, sizes, and READMEs": dict(npx_exit=0, readme="[Missing](nope.md)\n"),
            "Script tests": dict(npx_exit=0, test_body="self.fail('broken')"),
        }
        for step, kwargs in cases.items():
            with self.subTest(step), tempfile.TemporaryDirectory() as d:
                r = self.check(d, **kwargs)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(f"Failed: {step}", r.stdout)

    def test_missing_node_says_what_to_install_and_runs_the_rest(self):
        # #75
        with tempfile.TemporaryDirectory() as d:
            r = self.check(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("npx not found. Install Node.js 22 (see .nvmrc)", r.stdout)
            self.assertIn("== Script tests", r.stdout)
            self.assertTrue(r.stdout.rstrip().endswith("Failed: Markdown lint"), r.stdout)

    def test_missing_lint_install_says_to_run_npm_ci_and_runs_the_rest(self):
        # #120: lint runs only the locked version, so a checkout without npm ci gets told what to do
        with tempfile.TemporaryDirectory() as d:
            r = self.check(d, npx_exit=0, installed=False)
            self.assertEqual(r.returncode, 1)
            self.assertIn("markdownlint-cli2 isn't installed. Run npm ci", r.stdout)
            self.assertIn("== Script tests", r.stdout)
            self.assertTrue(r.stdout.rstrip().endswith("Failed: Markdown lint"), r.stdout)

    def test_install_that_differs_from_the_lockfile_says_to_run_npm_ci_again(self):
        # #131: after a pull that bumped the linter, check.py linted with the old version and passed
        with tempfile.TemporaryDirectory() as d:
            r = self.check(d, npx_exit=0, installed="0.9.0")
            self.assertEqual(r.returncode, 1)
            self.assertIn("node_modules doesn't match package-lock.json. Run npm ci again", r.stdout)
            self.assertIn("== Script tests", r.stdout)
            self.assertTrue(r.stdout.rstrip().endswith("Failed: Markdown lint"), r.stdout)

    def test_help_prints_usage_and_runs_no_check(self):
        # #137: --help used to run every check
        with tempfile.TemporaryDirectory() as d:
            script = copy_script(d, "check.py")
            r = subprocess.run([sys.executable, script, "--help"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Run from the repository root: python scripts/check.py", r.stdout)
            self.assertNotIn("==", r.stdout)


class MarkdownLintConfigTest(unittest.TestCase):
    def test_lint_tool_is_pinned_and_locked(self):
        # #120: an exact pin in package.json, the same version in package-lock.json, so Dependabot can move both
        with open(os.path.join(ROOT, "package.json"), encoding="utf-8") as f:
            pinned = json.load(f)["devDependencies"]["markdownlint-cli2"]
        with open(os.path.join(ROOT, "package-lock.json"), encoding="utf-8") as f:
            locked = json.load(f)["packages"]["node_modules/markdownlint-cli2"]["version"]
        self.assertRegex(pinned, r"^\d+\.\d+\.\d+$")
        self.assertEqual(pinned, locked)

    def test_lint_skips_what_gitignore_excludes(self):
        # #97: a local .venv with Markdown files used to fail the lint step
        with open(os.path.join(ROOT, ".markdownlint-cli2.jsonc"), encoding="utf-8") as f:
            text = f.read()
        self.assertRegex(text, r'"gitignore"\s*:\s*true')


if __name__ == "__main__":
    unittest.main()
