"""Checks the rules in CONTRIBUTING.md that a linter can't: links and anchors, file names, sizes, READMEs that list
their files, image links, and attribution tags on website links.

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
# Inline links and images (with an optional title), reference definitions, and HTML src/href attributes
LINK = re.compile(r"\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)"
                  r"|^[ \t]*\[[^\]]+\]:[ \t]*<?([^\s>]+)"
                  r"|\b(?:src|href)=[\"']([^\"']+)[\"']", re.MULTILINE)
HEADING = re.compile(r"^#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
# GitHub wraps every image that isn't already inside a link or <picture> in a link to the image file
EMPTY_ALT_IMG = re.compile(r"<img\b[^>]*\balt=(?:\"\"|'')[^>]*>|(?<!\[)!\[\]\(")
WRAPPER = re.compile(r"<picture\b.*?</picture>|<a\b[^>]*>.*?</a>|\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", re.DOTALL)
WEBSITE_PAGE = re.compile(r"https://(?:www\.)?solarityai\.com(?=[/?#\s)\"'<>\]]|$)(?!/assets/)[^\s)\"'<>]*")

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


def slug(heading):
    """The anchor GitHub gives a heading: lowercase, punctuation dropped, spaces as hyphens."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", re.sub(r"<[^>]+>", "", heading))
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def anchors(text):
    found, seen = set(), {}
    for heading in HEADING.findall(FENCE.sub("", text)):
        base = slug(heading)
        n = seen.get(base, 0)
        seen[base] = n + 1
        found.add(base if n == 0 else f"{base}-{n}")
    return found | set(re.findall(r"\b(?:id|name)=[\"']([^\"']+)[\"']", text))


errors = []
files = list_files()
# Exact names, so a link whose case differs fails here as it does on GitHub, even on Windows and macOS
known = {"."} | set(files) | {"/".join(f.split("/")[:i]) for f in files for i in range(1, f.count("/") + 1)}
texts = {}
for rel in files:
    if rel.endswith(".md"):
        with open(rel, "rb") as f:
            raw = f.read()
        try:
            texts[rel] = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{rel}: not UTF-8; save it as UTF-8")

for d in sorted({os.path.dirname(f) for f in files if f.split("/")[0] in CONTENT_DIRS}):
    readme = f"{d}/README.md"
    if readme not in known:
        errors.append(f"{d}: folder has no README.md; say what its files are and how to use them")
        continue
    for f in files:
        if os.path.dirname(f) == d and f != readme and os.path.basename(f) not in texts.get(readme, ""):
            errors.append(f"{readme}: doesn't list {os.path.basename(f)}")

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

    if rel not in texts:
        continue
    text = texts[rel]
    if name == "README.md" and len(text.strip()) < 40:
        errors.append(f"{rel}: README is empty or a placeholder")
    for match in LINK.finditer(text):
        url = match.group(1) or match.group(2) or match.group(3)
        if url.startswith(("http://", "https://", "mailto:")):
            continue
        path, _, fragment = url.partition("#")
        target = rel
        if path:
            target = os.path.normpath(os.path.join(os.path.dirname(rel), path.split("?")[0])).replace(os.sep, "/")
        if target not in known:
            errors.append(f"{rel}: broken link to {url}")
            continue
        page = target if target.endswith(".md") else ("README.md" if target == "." else f"{target}/README.md")
        if fragment and page in texts and fragment not in anchors(texts[page]):
            errors.append(f"{rel}: broken link to {url} (no heading with that anchor)")
    wrappers = [m.span() for m in WRAPPER.finditer(text)]
    if any(not any(a <= m.start() < b for a, b in wrappers) for m in EMPTY_ALT_IMG.finditer(text)):
        errors.append(f"{rel}: an image with empty alt text becomes a link with no name on GitHub; wrap it in <picture>")
    if name == "README.md":
        for url in WEBSITE_PAGE.findall(text):
            if "utm_source=github" not in url:
                errors.append(f"{rel}: {url} needs utm_source=github&utm_medium=public-resources&utm_campaign=<page>")

for error in sorted(set(errors)):
    print(f"::error::{error}")
print(f"{len(set(errors))} problem(s) found")
sys.exit(1 if errors else 0)
