"""Brand and content rules from CLAUDE.md that are easy to regress. Run: python -m unittest discover -s tests"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THIS = "tests/test_content.py"  # quotes the wrong forms it looks for, so it skips itself
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,}).*?(?:^ {0,3}\1[`~]*[ \t\r]*$|\Z)", re.MULTILINE | re.DOTALL)  # as in check_docs.py
CODE_SPAN = re.compile(r"(`+)(?!`).+?(?<!`)\1(?!`)")


def repo_files(*suffixes):
    """Tracked and new files, minus anything .gitignore excludes, as scripts/check_docs.py lists them."""
    try:
        # git writes paths as UTF-8 whatever the system code page is (#132)
        out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, encoding="utf-8", check=True).stdout
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


def rendered(rel):
    """What GitHub renders as Markdown and HTML: code blocks blanked (line numbers kept) and code spans dropped."""
    return CODE_SPAN.sub("", FENCE.sub(lambda m: "\n" * m.group().count("\n"), read(rel)))


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
            for n, line in enumerate(rendered(rel).splitlines(), 1):
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

    def test_every_image_sets_width_and_height(self):
        # #146: with only a width, the browser can't reserve the height and the page shifts when the image loads
        hits = [f"{rel}:{n}" for rel in repo_files(".md")
                for n, line in enumerate(rendered(rel).splitlines(), 1)
                for tag in re.findall(r"<img\b[^>]*>", line)
                if not (re.search(r"\bwidth=", tag) and re.search(r"\bheight=", tag))]
        self.assertEqual(hits, [])

    def test_rendered_blanks_every_kind_of_code_fence(self):
        # #165: only ``` fences were blanked, so ~~~ and longer fences were read as page content
        text = "a\n~~~html\n<img src=x>\n~~~\nb\n````md\n```\n<img src=y>\n```\n````\nc\n"
        out = CODE_SPAN.sub("", FENCE.sub(lambda m: "\n" * m.group().count("\n"), text))
        self.assertNotIn("<img", out)
        self.assertEqual(out.split("\n").index("b"), text.split("\n").index("b"))


class TableLinkTest(unittest.TestCase):
    def test_links_in_tables_are_not_code_formatted(self):
        # #160: GitHub draws a code-formatted link on a grey box; in a striped table row that's 4.34:1, under WCAG's 4.5:1
        hits = [f"{rel}:{n}" for rel in repo_files(".md")
                for n, line in enumerate(FENCE.sub(lambda m: "\n" * m.group().count("\n"), read(rel)).splitlines(), 1)
                if line.lstrip().startswith("|") and re.search(r"\[`[^`\]]+`\]\(", line)]
        self.assertEqual(hits, [], "write [name](path), not a code-formatted name, inside tables")


class SourceOfTruthTest(unittest.TestCase):
    def test_colors_page_uses_the_website_names(self):
        # #129: solarityai.com's :root (2026-10-28) has --ember: #d9782f and --ink: #1a140e; the page had them swapped
        documented = {name: hexv for name, hexv in re.findall(r"\| ([A-Z][a-z]+(?: [a-z]+)?) \| `#([0-9A-F]{6})`", read("brand/colors/README.md"))}
        for name, hexv in (("Ember", "D9782F"), ("Ink", "1A140E"), ("Raised", "221C16"), ("Light gold", "FFCF7A")):
            self.assertEqual(documented.get(name), hexv, name)

    def test_privacy_summary_covers_visits(self):
        # #162: the policy's "What we receive" includes the IP address and browser type Cloudflare handles on every visit
        summary = read("legal-public/privacy-policy/README.md")
        self.assertNotIn("only what you choose to send", summary)
        self.assertIn("IP address and browser type", summary)


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

    def test_founder_photo_has_a_400_px_preview(self):
        # #145: the pages show the photo at 120-200 px, so they load this instead of the 800 px master
        with Image.open(os.path.join(ROOT, "press-kit/images/thumbs/ata-turhan-founder-400.jpg")) as small:
            self.assertEqual(small.size, (400, 400))
        for rel in ("press-kit/founder-bio/README.md", "press-kit/images/README.md"):
            self.assertNotRegex(read(rel), r'<img src="[^"]*ata-turhan-founder\.jpg"', rel)


if __name__ == "__main__":
    unittest.main()
