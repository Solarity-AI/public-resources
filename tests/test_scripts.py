"""Tests for the repository scripts. Run: python -m unittest discover -s tests"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")


def write(base, rel, text="x"):
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run(script, cwd, *args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd, capture_output=True, text=True)


def check_docs(d):
    return run("check_docs.py", d, d)


def copy_script(base, script):
    with open(os.path.join(SCRIPTS, script), encoding="utf-8") as f:
        write(base, f"scripts/{script}", f.read())
    return os.path.join(base, "scripts", script)


GOOD_README = "# Brand\n\nA useful description of this folder and its files.\n"
TAGS = "utm_source=github&utm_medium=public-resources&utm_campaign=brand"


class CheckDocsTest(unittest.TestCase):
    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Logo](logo.png)\n")
            write(d, "brand/logo.png")
            r = check_docs(d)
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_flags_bad_name_broken_link_and_empty_readme(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Missing](nope.md)\n")
            write(d, "brand/Bad Name.png")
            write(d, "careers/README.md", "x")
            r = check_docs(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("kebab-case", r.stdout)
            self.assertIn("broken link to nope.md", r.stdout)
            self.assertIn("README is empty", r.stdout)

    def test_query_string_links_resolve(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Download](logo.png?raw=true)\n")
            write(d, "brand/logo.png")
            self.assertEqual(check_docs(d).returncode, 0)

    def test_checks_the_repository_when_run_from_another_folder(self):
        # QA-02 (#83): run from scripts/, it used to walk only scripts/ and pass
        with tempfile.TemporaryDirectory() as d:
            script = copy_script(d, "check_docs.py")
            write(d, "brand/README.md", GOOD_README + "[Missing](nope.md)\n")
            r = subprocess.run([sys.executable, script], cwd=os.path.dirname(script), capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("broken link to nope.md", r.stdout)

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_ignored_folders_are_skipped(self):
        # QA-03 (#85): a local .venv used to fail the check
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            write(d, ".gitignore", ".venv/\n")
            write(d, "brand/README.md", GOOD_README)
            write(d, ".venv/lib/README.md", GOOD_README + "[Missing](nope.md)\n")
            self.assertEqual(check_docs(d).returncode, 0, check_docs(d).stdout)
            write(d, "careers/README.md", GOOD_README + "[New and untracked](gone.md)\n")
            self.assertIn("broken link to gone.md", check_docs(d).stdout)

    def test_decorative_images_must_not_become_unnamed_links(self):
        # QA-06 (#84): GitHub wraps a bare <img alt=""> in a link with no name
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/logo.png")
            write(d, "brand/README.md", GOOD_README + '<img src="logo.png" width="24" height="24" alt=""> Logo\n')
            r = check_docs(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("wrap it in <picture>", r.stdout)
            write(d, "brand/README.md", GOOD_README + '<picture><img src="logo.png" width="24" height="24" alt=""></picture> Logo\n')
            self.assertEqual(check_docs(d).returncode, 0, check_docs(d).stdout)

    def test_every_content_folder_needs_a_readme(self):
        # QA-07 (#88)
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README)
            write(d, "brand/swatches/night.png")
            r = check_docs(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("brand/swatches: folder has no README.md", r.stdout)

    def test_website_page_links_carry_attribution_tags(self):
        # QA-08 (#89): page links need utm tags; file downloads under /assets/ don't
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Press](https://solarityai.com/press/)\n")
            r = check_docs(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("https://solarityai.com/press/ needs utm_source", r.stdout)
            write(d, "brand/README.md", GOOD_README + f"[Press](https://solarityai.com/press/?{TAGS})\n"
                  "[ZIP](https://solarityai.com/assets/press/kit.zip)\n")
            self.assertEqual(check_docs(d).returncode, 0, check_docs(d).stdout)

    def test_href_titled_and_reference_links_are_checked(self):
        # #94: these link forms used to be skipped, so a broken one passed
        for link in ('<a href="missing.png">Missing</a>', '[Missing](missing.png "A title")',
                     "[Missing][ref]\n\n[ref]: missing.png"):
            with tempfile.TemporaryDirectory() as d:
                write(d, "brand/README.md", GOOD_README + link + "\n")
                r = check_docs(d)
                self.assertEqual(r.returncode, 1, link)
                self.assertIn("broken link to missing.png", r.stdout, link)

    def test_anchors_must_match_a_heading(self):
        # #95: a link to a missing heading lands at the top of the page on GitHub
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "## Logo files\n\n[Below](#logo-files)\n")
            write(d, "careers/README.md", GOOD_README + "[Logos](../brand/#logo-files)\n")
            self.assertEqual(check_docs(d).returncode, 0, check_docs(d).stdout)
            write(d, "careers/README.md", GOOD_README + "[Logos](../brand/#no-such-heading)\n[Here](#nope)\n")
            r = check_docs(d)
            self.assertIn("broken link to ../brand/#no-such-heading", r.stdout)
            self.assertIn("broken link to #nope", r.stdout)

    def test_link_case_must_match_exactly(self):
        # #96: Windows and macOS ignore case, GitHub and CI don't
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/logo.png")
            write(d, "brand/README.md", GOOD_README + "[Logo](Logo.png) logo.png\n")
            self.assertIn("broken link to Logo.png", check_docs(d).stdout)

    def test_markdown_that_is_not_utf8_is_reported(self):
        # #98: used to crash with a UnicodeDecodeError traceback
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README)
            os.makedirs(os.path.join(d, "careers"))
            with open(os.path.join(d, "careers", "README.md"), "wb") as f:
                f.write("# Café\n\nSaved in Latin-1 instead of UTF-8, as an editor might.\n".encode("latin-1"))
            r = check_docs(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("careers/README.md: not UTF-8", r.stdout)
            self.assertNotIn("Traceback", r.stderr)

    def test_picture_with_source_passes_and_single_quoted_alt_is_flagged(self):
        # #100
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/logo.png")
            write(d, "brand/README.md", GOOD_README + '<picture><source srcset="logo.png">'
                  '<img src="logo.png" width="24" height="24" alt=""></picture> Logo\n')
            self.assertEqual(check_docs(d).returncode, 0, check_docs(d).stdout)
            write(d, "brand/README.md", GOOD_README + "<img src='logo.png' width='24' height='24' alt=''> Logo\n")
            self.assertIn("wrap it in <picture>", check_docs(d).stdout)

    def test_website_links_without_slash_or_with_www_need_tags(self):
        # #101
        for url in ("https://solarityai.com", "https://www.solarityai.com/press/"):
            with tempfile.TemporaryDirectory() as d:
                write(d, "brand/README.md", GOOD_README + f"[Site]({url})\n")
                self.assertIn(f"{url} needs utm_source", check_docs(d).stdout, url)

    def test_readme_lists_every_file_in_its_folder(self):
        # #102: CONTRIBUTING says every folder's README lists its files
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Logo](logo.png)\n")
            write(d, "brand/logo.png")
            write(d, "brand/banner.png")
            r = check_docs(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("brand/README.md: doesn't list banner.png", r.stdout)

    def test_files_over_1_mb_are_flagged(self):
        # #114
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Poster](poster.png)\n")
            write(d, "brand/poster.png", "x" * 1_000_001)
            r = check_docs(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("brand/poster.png: 1,000,001 bytes; put files over 1 MB in a GitHub Release", r.stdout)
            write(d, "brand/poster.png", "x" * 1_000_000)
            self.assertEqual(check_docs(d).returncode, 0, check_docs(d).stdout)

    def test_folder_names_must_be_kebab_case(self):
        # #114
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README)
            write(d, "brand/Old_Logos/README.md", GOOD_README + "[Logo](logo.png)\n")
            write(d, "brand/Old_Logos/logo.png")
            r = check_docs(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("brand/Old_Logos/logo.png: folder 'Old_Logos' must be lowercase kebab-case", r.stdout)

    def test_readme_must_list_the_whole_file_name(self):
        # #133: gold.png counted as listed because light-gold.png contains it
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/gold.png")
            write(d, "brand/light-gold.png")
            write(d, "brand/README.md", GOOD_README + "`light-gold.png`\n")
            self.assertIn("brand/README.md: doesn't list gold.png", check_docs(d).stdout)
            for listed in ("[Gold](./gold.png)", "[Gold](/brand/gold.png)", "[Gold](../brand/gold.png)"):
                write(d, "brand/README.md", GOOD_README + f"`light-gold.png` and {listed}\n")
                self.assertEqual(check_docs(d).returncode, 0, listed + check_docs(d).stdout)

    def test_links_with_single_quoted_or_parenthesized_titles_are_checked(self):
        # #134: CommonMark allows "title", 'title' and (title); #94 covered only the first
        for link in ("[Missing](missing.png 'A title')", "[Missing](missing.png (A title))"):
            with tempfile.TemporaryDirectory() as d:
                write(d, "brand/README.md", GOOD_README + link + "\n")
                self.assertIn("broken link to missing.png", check_docs(d).stdout, link)

    def test_link_syntax_inside_code_is_not_a_link(self):
        # #135: GitHub shows code as text, so an example link can't be broken
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "Write links like `[text](other-file.md)`.\n\n"
                  "```md\n[text](other-file.md)\n```\n")
            self.assertEqual(check_docs(d).returncode, 0, check_docs(d).stdout)
            write(d, "brand/README.md", GOOD_README + "`code` and then [text](other-file.md)\n")
            self.assertIn("broken link to other-file.md", check_docs(d).stdout)

    def test_root_relative_links_resolve_from_the_repository_root(self):
        # #136: GitHub resolves a link that starts with / from the repository root
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/logo.png")
            write(d, "brand/README.md", GOOD_README + "[Logo](logo.png)\n")
            write(d, "careers/README.md", GOOD_README + "[Logo](/brand/logo.png) [Brand](/brand/)\n")
            self.assertEqual(check_docs(d).returncode, 0, check_docs(d).stdout)
            write(d, "careers/README.md", GOOD_README + "[Gone](/brand/gone.png)\n")
            self.assertIn("broken link to /brand/gone.png", check_docs(d).stdout)

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_non_ascii_names_and_text_are_reported_on_any_console(self):
        # #132: on Windows, git's UTF-8 file list was read as cp1252 (files skipped or a crash),
        # and a message with a character the console can't show crashed the check
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            write(d, "brand/README.md", GOOD_README + "[Logo](Café.png) [Mark](ā-mark.png) [Next](→next.md)\n")
            write(d, "brand/Café.png")
            write(d, "brand/ā-mark.png")
            r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_docs.py"), d], capture_output=True,
                               env=dict(os.environ, PYTHONIOENCODING="ascii"))
            out = r.stdout.decode("ascii", "replace")
            self.assertNotIn(b"Traceback", r.stderr)
            self.assertIn("brand/Caf\\xe9.png: file name must be lowercase kebab-case", out)
            self.assertIn("brand/\\u0101-mark.png: file name must be lowercase kebab-case", out)
            self.assertIn("broken link to \\u2192next.md", out)

    def test_help_and_a_missing_folder_get_a_message_not_a_traceback(self):
        # #137
        r = run("check_docs.py", ROOT, "--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Run: python scripts/check_docs.py [root]", r.stdout)
        with tempfile.TemporaryDirectory() as d:
            r = run("check_docs.py", d, os.path.join(d, "missing"))
            self.assertEqual(r.returncode, 1)
            self.assertIn("missing: no such folder", r.stderr)
            self.assertNotIn("Traceback", r.stderr)


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


class BuildPressKitTest(unittest.TestCase):
    def test_zip_entries_have_the_same_metadata_on_every_os(self):
        # #92: Python records the creating OS in each entry (0 on Windows, 3 elsewhere)
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/logos/solarity-sun-mark.png", "png")
            self.assertEqual(run("build_press_kit.py", d, "9999.01").returncode, 0)
            with zipfile.ZipFile(os.path.join(d, "dist", "solarity-ai-brand-and-press-kit-9999.01.zip")) as z:
                for info in z.infolist():
                    self.assertEqual((info.create_system, info.date_time, info.external_attr >> 16),
                                     (3, (2026, 1, 1, 0, 0, 0), 0o644), info.filename)

    def test_same_files_give_the_same_zip(self):
        # QA-01 (#82): file times from the checkout used to change the hash
        digests = []
        for mtime in (1_000_000_000, 1_700_000_000):
            with tempfile.TemporaryDirectory() as d:
                write(d, "brand/logos/solarity-sun-mark.png", "png")
                os.utime(os.path.join(d, "brand/logos/solarity-sun-mark.png"), (mtime, mtime))
                self.assertEqual(run("build_press_kit.py", d, "9999.01").returncode, 0)
                with open(os.path.join(d, "dist", "solarity-ai-brand-and-press-kit-9999.01.zip.sha256"), encoding="utf-8") as f:
                    digests.append(f.read())
        self.assertEqual(digests[0], digests[1])

    def test_rejects_versions_that_are_not_year_and_month(self):
        # QA-05 (#87)
        # #99: 2026.13, 2026.00 and the newline; #139: full-width and Arabic-Indic digits that only look like 2026
        for bad in ("", "../escaped", "2026.10/x", "latest", "2026.13", "2026.00", "2026.10\n", "２０２６.10", "٢٠٢٦.10"):
            with tempfile.TemporaryDirectory() as d:
                write(d, "brand/logos/solarity-sun-mark.png", "png")
                r = run("build_press_kit.py", d, bad)
                self.assertEqual(r.returncode, 1, bad)
                self.assertIn("Usage", r.stderr)
                self.assertFalse(os.path.exists(os.path.join(d, "dist")), bad)

    def test_zip_and_checksum(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/logos/solarity-sun-mark.png", "png")
            r = run("build_press_kit.py", d, "9999.01")
            self.assertEqual(r.returncode, 0, r.stderr)
            out = os.path.join(d, "dist", "solarity-ai-brand-and-press-kit-9999.01.zip")
            names = zipfile.ZipFile(out).namelist()
            self.assertIn("solarity-ai-brand-and-press-kit/README.txt", names)
            self.assertIn("solarity-ai-brand-and-press-kit/brand/logos/solarity-sun-mark.png", names)
            with open(out, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            with open(out + ".sha256", encoding="utf-8") as f:
                self.assertEqual(f.read(), f"{digest}  solarity-ai-brand-and-press-kit-9999.01.zip\n")

    def test_requires_version(self):
        with tempfile.TemporaryDirectory() as d:
            r = run("build_press_kit.py", d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("Usage", r.stderr)

    def test_zip_holds_every_asset_type_and_nothing_else(self):
        # #116: one file for each pattern, so a typo that drops a whole asset type fails here
        assets = ["brand/logos/a.png", "brand/banner/a.png", "brand/typography/a.png", "brand/social-media/a.jpg",
                  "brand/colors/swatches/a.png", "press-kit/images/a.jpg", "press-kit/images/app-icons/a.png",
                  "press-kit/images/screens/a.jpg"]
        with tempfile.TemporaryDirectory() as d:
            for rel in assets + ["brand/logos/README.md", "press-kit/images/notes.txt"]:
                write(d, rel)
            self.assertEqual(run("build_press_kit.py", d, "9999.01").returncode, 0)
            with zipfile.ZipFile(os.path.join(d, "dist", "solarity-ai-brand-and-press-kit-9999.01.zip")) as z:
                names = set(z.namelist())
            root = "solarity-ai-brand-and-press-kit/"
            self.assertEqual(names, {root + "README.txt"} | {root + a for a in assets})

    def test_no_assets_is_a_clear_error(self):
        # #116: run from the wrong folder
        with tempfile.TemporaryDirectory() as d:
            r = run("build_press_kit.py", d, "9999.01")
            self.assertEqual(r.returncode, 1)
            self.assertIn("No assets found. Run this from the repository root.", r.stderr)
            self.assertFalse(os.path.exists(os.path.join(d, "dist")))


try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


def assets_module():
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    import generate_assets
    return generate_assets


@contextlib.contextmanager
def inside(d):
    """Run generate_assets functions, which write repo-relative paths, in a temp folder."""
    cwd = os.getcwd()
    os.chdir(d)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            yield
    finally:
        os.chdir(cwd)


@unittest.skipUnless(HAVE_PIL, "Pillow not installed (pip install -r requirements.txt)")
class FontVerificationTest(unittest.TestCase):
    def test_tampered_font_is_rejected(self):
        sys.path.insert(0, SCRIPTS)
        import generate_assets as g
        with tempfile.TemporaryDirectory() as d:
            old = g.FONT_DIR
            g.FONT_DIR = d
            try:
                for name in g.FONTS:
                    write(d, name, "not the real font")
                with self.assertRaises(SystemExit) as e:
                    g.fetch_fonts()
                self.assertIn("SHA-256 mismatch", str(e.exception))
                self.assertFalse(os.path.exists(os.path.join(d, next(iter(g.FONTS)))))
            finally:
                g.FONT_DIR = old

    def test_runs_from_the_repository_root_wherever_it_starts(self):
        # QA-04 (#86): from scripts/ it used to download fonts into scripts/.cache, then crash
        with tempfile.TemporaryDirectory() as d:
            script = copy_script(d, "generate_assets.py")
            for name in ("Newsreader.ttf", "Manrope.ttf"):
                write(d, f".cache/fonts/{name}", "not the real font")
            r = subprocess.run([sys.executable, script], cwd=os.path.dirname(script), capture_output=True, text=True)
            self.assertIn("SHA-256 mismatch", r.stderr)
            self.assertFalse(os.path.exists(os.path.join(d, "scripts", ".cache")))


class GenerateAssetsCommandTest(unittest.TestCase):
    """The command line, which needs neither Pillow nor the network."""

    def test_help_prints_usage_and_writes_nothing(self):
        # #137: --help used to download fonts and rewrite 34 images
        with tempfile.TemporaryDirectory() as d:
            script = copy_script(d, "generate_assets.py")
            r = subprocess.run([sys.executable, script, "--help"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Regenerate every derived image from the masters.", r.stdout)
            self.assertEqual(os.listdir(d), ["scripts"])

    def test_missing_pillow_says_what_to_install(self):
        # #138: a stand-in PIL that fails to import, as on a Python without Pillow
        with tempfile.TemporaryDirectory() as d:
            script = copy_script(d, "generate_assets.py")
            write(d, "fake/PIL/__init__.py", "raise ImportError(\"No module named 'PIL'\")\n")
            r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                               env=dict(os.environ, PYTHONPATH=os.path.join(d, "fake")))
            self.assertEqual(r.returncode, 1)
            self.assertIn("Run: pip install -r requirements.txt", r.stderr)
            self.assertNotIn("Traceback", r.stderr)
            self.assertEqual(sorted(os.listdir(d)), ["fake", "scripts"])


class BrokenDownload(io.BytesIO):
    def read(self, *args):
        raise OSError("connection reset")


@unittest.skipUnless(HAVE_PIL, "Pillow not installed (pip install -r requirements.txt)")
class FontDownloadTest(unittest.TestCase):
    """The download path, with urlopen stubbed: no network in tests (#110)."""

    def setUp(self):
        self.g = assets_module()
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        fonts = {"Test.ttf": ("https://example.invalid/Test.ttf", hashlib.sha256(b"font bytes").hexdigest())}
        for name, value in (("FONT_DIR", self.dir), ("FONTS", fonts)):
            patcher = mock.patch.object(self.g, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_download_is_verified_and_kept(self):
        with mock.patch("urllib.request.urlopen", return_value=io.BytesIO(b"font bytes")) as urlopen, \
                contextlib.redirect_stdout(io.StringIO()):
            self.g.fetch_fonts()
        urlopen.assert_called_once_with("https://example.invalid/Test.ttf", timeout=30)
        self.assertEqual(os.listdir(self.dir), ["Test.ttf"])

    def test_failed_download_says_what_to_do_and_leaves_no_partial_file(self):
        # #76: a clear message instead of a traceback, and no half-written font
        for name, stub in (("on connect", dict(side_effect=OSError("timed out"))),
                           ("mid-download", dict(return_value=BrokenDownload()))):
            with self.subTest(name), mock.patch("urllib.request.urlopen", **stub), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as e:
                    self.g.fetch_fonts()
                self.assertIn("Couldn't download Test.ttf", str(e.exception))
                self.assertIn("Check your connection, or save https://example.invalid/Test.ttf", str(e.exception))
                self.assertEqual(os.listdir(self.dir), [])


@unittest.skipUnless(HAVE_PIL, "Pillow not installed (pip install -r requirements.txt)")
class GeneratedImagesTest(unittest.TestCase):
    def test_glow_runs_from_navy_to_deep_navy(self):
        # #109: brand/colors documents Navy #1F225C at the center and Deep navy #0D1120 toward the edges
        g = assets_module()
        self.assertEqual(g.navy_color(0), (0x1F, 0x22, 0x5C))
        self.assertEqual(g.navy_color(0.86), (0x0D, 0x11, 0x20))
        self.assertEqual(g.navy_color(3), g.navy_color(1))

    def test_sun_mark_sits_on_logo_navy_not_the_website_black(self):
        # #109: CLAUDE.md lists this as easy to regress; Night #0F0D0B is warm, the logo navy is blue
        g = assets_module()
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "brand", "logos"))
            with inside(d):
                g.logos(Image.new("RGBA", (64, 64)))  # a transparent mark, so only the background shows
            with Image.open(os.path.join(d, "brand/logos/solarity-sun-mark-on-navy.png")) as im:
                size, center, corner = im.size, im.getpixel((600, 600)), im.getpixel((0, 0))
            self.assertEqual(size, (1200, 1200))
            self.assertTrue(all(abs(a - b) <= 3 for a, b in zip(center, (0x1F, 0x22, 0x5C))), center)
            r, gr, b = corner
            self.assertTrue(b > r + 15 and b > gr + 15 and max(corner) < 64, f"corner {corner} isn't dark navy")
            for s in (512, 192):
                with Image.open(os.path.join(d, f"brand/logos/solarity-sun-mark-on-navy-{s}.png")) as im:
                    self.assertEqual(im.size, (s, s))

    def test_thumbnails_are_96_px_icons_and_300_px_wide_screens(self):
        # #113
        g = assets_module()
        with tempfile.TemporaryDirectory() as d:
            images = os.path.join(d, "press-kit", "images")
            for sub in ("app-icons/thumbs", "screens/thumbs"):
                os.makedirs(os.path.join(images, sub))
            Image.new("RGBA", (200, 200), (255, 0, 0, 255)).save(os.path.join(images, "app-icons", "demo-icon.png"))
            Image.new("RGB", (600, 1300), (0, 0, 255)).save(os.path.join(images, "screens", "demo-screen.jpg"))
            with inside(d):
                g.thumbnails()
            with Image.open(os.path.join(images, "app-icons", "thumbs", "demo-icon-96.png")) as im:
                self.assertEqual((im.size, im.mode), ((96, 96), "RGBA"))
            with Image.open(os.path.join(images, "screens", "thumbs", "demo-screen-300.jpg")) as im:
                self.assertEqual(im.size, (300, 650))


if __name__ == "__main__":
    unittest.main()
