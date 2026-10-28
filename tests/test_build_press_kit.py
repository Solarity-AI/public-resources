"""Tests for scripts/build_press_kit.py. Run: python -m unittest discover -s tests"""
import hashlib
import os
import sys
import tempfile
import unittest
import zipfile

# support.py sits beside this file; discover puts this folder on sys.path, and this covers tests.<module> runs too
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from support import run, write


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


if __name__ == "__main__":
    unittest.main()
