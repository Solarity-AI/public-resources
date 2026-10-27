"""Checks the rules in CONTRIBUTING.md that a linter can't: links, file names, sizes, READMEs, image links, and
attribution tags on website links.

Run: python scripts/check_docs.py [root]   (root defaults to this repository, wherever you run it from)
"""
import os
import re
import subprocess
import sys

CONTENT_DIRS = ["brand", "careers", "demos", "docs", "legal-public", "one-pagers", "pitch-decks", "press-kit"]
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+)+$")
ALLOWED_NAMES = {"README.md"}
MAX_BYTES = 1_000_000
LINK = re.compile(r"\]\(([^)\s]+)\)|src=\"([^\"]+)\"")
# GitHub wraps every <img> that isn't already inside a link or <picture> in a link to the image file
BARE_IMG = re.compile(r"<img\b[^>]*\balt=\"\"[^>]*>")
WRAPPED_IMG = re.compile(r"<(picture|a)\b[^>]*>\s*<img\b[^>]*\balt=\"\"[^>]*>\s*</\1>")
WEBSITE_PAGE = re.compile(r"https://solarityai\.com/(?!assets/)[^\s)\"'>]*")

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(root)


def list_files():
    """Tracked and new files, minus anything .gitignore excludes (a local .venv, dist/, .cache/)."""
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout
        return sorted(f for f in out.split("\0") if f and os.path.isfile(f))
    except (OSError, subprocess.CalledProcessError):
        pass  # not a git checkout, or git isn't installed
    files = []
    for top, dirs, names in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules"}]
        files += [os.path.relpath(os.path.join(top, n)).replace(os.sep, "/") for n in names]
    return sorted(files)


errors = []
files = list_files()

for d in sorted({os.path.dirname(f) for f in files if f.split("/")[0] in CONTENT_DIRS}):
    if not os.path.exists(os.path.join(d, "README.md")):
        errors.append(f"{d}: folder has no README.md; say what its files are and how to use them")

for rel in files:
    name = os.path.basename(rel)

    if rel.split("/")[0] in CONTENT_DIRS:
        if name not in ALLOWED_NAMES and not KEBAB.match(name):
            errors.append(f"{rel}: file name must be lowercase kebab-case")
        for part in rel.split("/")[:-1]:
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", part):
                errors.append(f"{rel}: folder '{part}' must be lowercase kebab-case")
        if os.path.getsize(rel) > MAX_BYTES:
            errors.append(f"{rel}: {os.path.getsize(rel):,} bytes; put files over 1 MB in a GitHub Release")

    if name.endswith(".md"):
        with open(rel, encoding="utf-8") as f:
            text = f.read()
        if name == "README.md" and len(text.strip()) < 40:
            errors.append(f"{rel}: README is empty or a placeholder")
        for match in LINK.finditer(text):
            url = match.group(1) or match.group(2)
            if url.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(rel), url.split("#")[0].split("?")[0]))
            if not os.path.exists(target):
                errors.append(f"{rel}: broken link to {url}")
        if len(BARE_IMG.findall(text)) > len(WRAPPED_IMG.findall(text)):
            errors.append(f"{rel}: an <img alt=\"\"> becomes a link with no name on GitHub; wrap it in <picture>")
        if name == "README.md":
            for url in WEBSITE_PAGE.findall(text):
                if "utm_source=github" not in url:
                    errors.append(f"{rel}: {url} needs utm_source=github&utm_medium=public-resources&utm_campaign=<page>")

for error in sorted(set(errors)):
    print(f"::error::{error}")
print(f"{len(set(errors))} problem(s) found")
sys.exit(1 if errors else 0)
