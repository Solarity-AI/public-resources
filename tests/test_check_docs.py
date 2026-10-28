"""Tests for scripts/check_docs.py. Run: python -m unittest discover -s tests"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

# support.py sits beside this file; discover puts this folder on sys.path, and this covers tests.<module> runs too
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from support import GOOD_README, ROOT, SCRIPTS, TAGS, check_docs, copy_script, run, write


class CheckDocsTest(unittest.TestCase):
    def assert_passes(self, d, msg=""):
        r = check_docs(d)  # once, so the message shows the run that failed
        self.assertEqual(r.returncode, 0, msg + r.stdout)

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
            self.assert_passes(d)

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
            self.assert_passes(d)
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
            self.assert_passes(d)

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
            self.assert_passes(d)

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
            self.assert_passes(d)
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
            self.assert_passes(d)
            write(d, "brand/README.md", GOOD_README + "<img src='logo.png' width='24' height='24' alt=''> Logo\n")
            self.assertIn("wrap it in <picture>", check_docs(d).stdout)

    def test_website_links_without_slash_or_with_www_need_tags(self):
        # #101
        for url in ("https://solarityai.com", "https://www.solarityai.com/press/"):
            with tempfile.TemporaryDirectory() as d:
                write(d, "brand/README.md", GOOD_README + f"[Site]({url})\n")
                self.assertIn(f"{url} needs utm_source", check_docs(d).stdout, url)

    def test_website_links_need_every_attribution_tag_by_its_exact_name(self):
        # #126: only utm_source=github was looked for, so a link missing the medium or campaign passed
        for query in ("utm_source=github", "utm_source=github&utm_medium=public-resources",
                      "utm_source=github&utm_campaign=brand", "utm_medium=public-resources&utm_campaign=brand",
                      "utm_source=github&utm_medium=public-resources&utm_campaign=",
                      "utm_source=github&utm_medium=email&utm_campaign=brand",
                      "xutm_source=github&xutm_medium=public-resources&utm_campaign=brand"):
            with tempfile.TemporaryDirectory() as d:
                write(d, "brand/README.md", GOOD_README + f"[Press](https://solarityai.com/press/?{query})\n")
                r = check_docs(d)
                self.assertEqual(r.returncode, 1, query)
                self.assertIn(f"https://solarityai.com/press/?{query} needs utm_source", r.stdout, query)
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + f"[Contact](https://solarityai.com/contact/?type=Investor&{TAGS}#form)\n"
                  f'<a href="https://solarityai.com/?{TAGS.replace("&", "&amp;")}">Site</a>\n')
            self.assert_passes(d)

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
            self.assert_passes(d)

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
                self.assert_passes(d, listed)

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
            self.assert_passes(d)
            write(d, "brand/README.md", GOOD_README + "`code` and then [text](other-file.md)\n")
            self.assertIn("broken link to other-file.md", check_docs(d).stdout)

    def test_root_relative_links_resolve_from_the_repository_root(self):
        # #136: GitHub resolves a link that starts with / from the repository root
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/logo.png")
            write(d, "brand/README.md", GOOD_README + "[Logo](logo.png)\n")
            write(d, "careers/README.md", GOOD_README + "[Logo](/brand/logo.png) [Brand](/brand/)\n")
            self.assert_passes(d)
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


if __name__ == "__main__":
    unittest.main()
