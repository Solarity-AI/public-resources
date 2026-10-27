"""Brand and content rules from CLAUDE.md that are easy to regress. Run: python -m unittest discover -s tests"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THIS = "tests/test_content.py"  # quotes the wrong forms it looks for, so it skips itself
FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def repo_files(*suffixes):
    """Tracked and new files, minus anything .gitignore excludes, as scripts/check_docs.py lists them."""
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        files = [f for f in out.split("\0") if f]
    except (OSError, subprocess.CalledProcessError):
        files = []
        for top, dirs, names in os.walk(ROOT):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"node_modules", "dist"}]
            files += [os.path.relpath(os.path.join(top, n), ROOT).replace(os.sep, "/") for n in names]
    return sorted(f for f in files if f.endswith(suffixes) and f != THIS and os.path.isfile(os.path.join(ROOT, f)))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as f:
        return f.read()


def lines(rel):
    return enumerate(read(rel).splitlines(), 1)


class FounderTitleTest(unittest.TestCase):
    def test_title_is_founder_never_ceo(self):
        # #108: the founder's request (2026-10-26). CHANGELOG.md keeps the history; CLAUDE.md states the rule.
        hits = [f"{rel}:{n}" for rel in repo_files(".md", ".py", ".txt", ".yml")
                if rel not in ("CHANGELOG.md", "CLAUDE.md")
                for n, line in lines(rel) if re.search(r"\bCEO\b", line)]
        self.assertEqual(hits, [], "Ata Turhan's title is Founder")


class NameTest(unittest.TestCase):
    def test_company_name_is_two_words(self):
        # #115: the brand guidelines list the wrong forms on a "- Not:" line
        hits = [f"{rel}:{n}" for rel in repo_files(".md") for n, line in lines(rel)
                if re.search(r"SolarityAI|Solarity Ai\b|Solarity\.ai", line) and not line.startswith("- Not:")]
        self.assertEqual(hits, [], "write Solarity AI, two words")

    def test_only_fitness_is_always_named_with_fitness_max(self):
        # #115: the app store name never stands alone (#16)
        hits = [f"{rel}:{n}" for rel in repo_files(".md", ".py", ".txt") for n, line in lines(rel)
                if "Only Fitness" in line and "Fitness Max" not in line]
        self.assertEqual(hits, [], 'write "Fitness Max (listed as Only Fitness)"')


class TableImageTest(unittest.TestCase):
    def test_table_images_set_width_and_height(self):
        # #111: GitHub collapses an image in a table on phones unless it sets both (#29)
        hits, checked = [], 0
        for rel in repo_files(".md"):
            text = FENCE.sub(lambda m: "\n" * m.group().count("\n"), read(rel))
            for n, line in enumerate(text.splitlines(), 1):
                if not line.lstrip().startswith("|"):
                    continue
                for tag in re.findall(r"<img\b[^>]*>", line):
                    checked += 1
                    if not (re.search(r"\bwidth=", tag) and re.search(r"\bheight=", tag)):
                        hits.append(f"{rel}:{n}")
                if "![" in line:
                    hits.append(f"{rel}:{n}: Markdown image syntax can't set a size; use <img> with width and height")
        self.assertGreater(checked, 0)
        self.assertEqual(hits, [])


try:
    from PIL import Image
except ImportError:
    Image = None


@unittest.skipUnless(Image, "Pillow not installed (pip install -r requirements.txt)")
class GeneratedAssetsTest(unittest.TestCase):
    def test_swatches_match_the_documented_colors(self):
        # #112: the hex in brand/colors/README.md, SWATCHES in generate_assets.py, and the PNG all agree
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import generate_assets
        documented = dict(re.findall(r"swatches/([a-z-]+)\.png.*?`#([0-9A-F]{6})`", read("brand/colors/README.md")))
        self.assertEqual(documented, generate_assets.SWATCHES)
        folder = os.path.join(ROOT, "brand", "colors", "swatches")
        self.assertEqual({f[:-4] for f in os.listdir(folder) if f.endswith(".png")}, set(documented))
        for name, hexv in documented.items():
            with Image.open(os.path.join(folder, f"{name}.png")) as im:
                rgb = im.convert("RGB")
            self.assertEqual((rgb.size, rgb.getpixel((24, 24))), ((48, 48), tuple(int(hexv[i:i + 2], 16) for i in (0, 2, 4))), name)

    def test_every_master_has_a_thumbnail(self):
        # #113: icons get a 96 px PNG, screens a 300 px wide JPEG; run scripts/generate_assets.py after adding a master
        for folder, suffix, thumb_suffix in (("press-kit/images/app-icons", "-icon.png", "-icon-96.png"),
                                             ("press-kit/images/screens", ".jpg", "-300.jpg")):
            path = os.path.join(ROOT, folder)
            masters = sorted(f for f in os.listdir(path) if f.endswith(suffix))
            thumbs = sorted(f for f in os.listdir(os.path.join(path, "thumbs")) if f.endswith(thumb_suffix))
            self.assertTrue(masters, folder)
            self.assertEqual(thumbs, [m[:-len(suffix)] + thumb_suffix for m in masters], folder)
            for m in masters:
                with Image.open(os.path.join(path, m)) as big, \
                        Image.open(os.path.join(path, "thumbs", m[:-len(suffix)] + thumb_suffix)) as small:
                    width, height = (96, 96) if suffix == "-icon.png" else (300, round(big.height * 300 / big.width))
                    self.assertEqual(small.size, (width, height), m)


if __name__ == "__main__":
    unittest.main()
