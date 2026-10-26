"""Tests for the repository scripts. Run: python -m unittest discover -s tests"""
import hashlib
import os
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


GOOD_README = "# Brand\n\nA useful description of this folder and its files.\n"


class CheckDocsTest(unittest.TestCase):
    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Logo](logo.png)\n")
            write(d, "brand/logo.png")
            r = run("check_docs.py", d)
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_flags_bad_name_broken_link_and_empty_readme(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Missing](nope.md)\n")
            write(d, "brand/Bad Name.png")
            write(d, "careers/README.md", "x")
            r = run("check_docs.py", d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("kebab-case", r.stdout)
            self.assertIn("broken link to nope.md", r.stdout)
            self.assertIn("README is empty", r.stdout)

    def test_query_string_links_resolve(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "brand/README.md", GOOD_README + "[Download](logo.png?raw=true)\n")
            write(d, "brand/logo.png")
            self.assertEqual(run("check_docs.py", d).returncode, 0)


class BuildPressKitTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
