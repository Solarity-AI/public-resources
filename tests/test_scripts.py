"""Tests for the repository scripts. Run: python -m unittest discover -s tests"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

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


class BuildPressKitTest(unittest.TestCase):
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
        for bad in ("", "../escaped", "2026.10/x", "latest"):
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


try:
    import PIL  # noqa: F401
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


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


if __name__ == "__main__":
    unittest.main()
