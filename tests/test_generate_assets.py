"""Tests for scripts/generate_assets.py. Run: python -m unittest discover -s tests"""
import contextlib
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

# support.py sits beside this file; discover puts this folder on sys.path, and this covers tests.<module> runs too
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from support import assets_module, copy_script, inside, write

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


@unittest.skipUnless(HAVE_PIL, "Pillow not installed (pip install -r requirements.txt)")
class FontVerificationTest(unittest.TestCase):
    def test_tampered_font_is_rejected(self):
        g = assets_module()
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

    def test_thumbnails_are_96_px_icons_300_px_wide_screens_and_a_400_px_founder_photo(self):
        # #113, #145
        g = assets_module()
        with tempfile.TemporaryDirectory() as d:
            images = os.path.join(d, "press-kit", "images")
            for sub in ("app-icons/thumbs", "screens/thumbs"):
                os.makedirs(os.path.join(images, sub))
            Image.new("RGBA", (200, 200), (255, 0, 0, 255)).save(os.path.join(images, "app-icons", "demo-icon.png"))
            Image.new("RGB", (600, 1300), (0, 0, 255)).save(os.path.join(images, "screens", "demo-screen.jpg"))
            Image.new("RGB", (800, 800), (0, 255, 0)).save(os.path.join(images, "ata-turhan-founder.jpg"))
            with inside(d):
                g.thumbnails()
            with Image.open(os.path.join(images, "app-icons", "thumbs", "demo-icon-96.png")) as im:
                self.assertEqual((im.size, im.mode), ((96, 96), "RGBA"))
            with Image.open(os.path.join(images, "screens", "thumbs", "demo-screen-300.jpg")) as im:
                self.assertEqual(im.size, (300, 650))
            with Image.open(os.path.join(images, "thumbs", "ata-turhan-founder-400.jpg")) as im:
                self.assertEqual(im.size, (400, 400))


if __name__ == "__main__":
    unittest.main()
