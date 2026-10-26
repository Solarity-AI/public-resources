"""Checks the rules in CONTRIBUTING.md that a linter can't: links, file names, sizes, empty READMEs.

Run from the repository root: python scripts/check_docs.py
"""
import os
import re
import sys

CONTENT_DIRS = ["brand", "careers", "demos", "docs", "legal-public", "one-pagers", "pitch-decks", "press-kit"]
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+)+$")
ALLOWED_NAMES = {"README.md"}
MAX_BYTES = 1_000_000
LINK = re.compile(r"\]\(([^)\s]+)\)|src=\"([^\"]+)\"")

errors = []

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in {".git", "node_modules"}]
    for name in files:
        path = os.path.join(root, name)
        rel = os.path.relpath(path).replace(os.sep, "/")

        if rel.split("/")[0] in CONTENT_DIRS:
            if name not in ALLOWED_NAMES and not KEBAB.match(name):
                errors.append(f"{rel}: file name must be lowercase kebab-case")
            for part in rel.split("/")[:-1]:
                if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", part):
                    errors.append(f"{rel}: folder '{part}' must be lowercase kebab-case")
            if os.path.getsize(path) > MAX_BYTES:
                errors.append(f"{rel}: {os.path.getsize(path):,} bytes; put files over 1 MB in a GitHub Release")

        if name.endswith(".md"):
            text = open(path, encoding="utf-8").read()
            if name == "README.md" and len(text.strip()) < 40:
                errors.append(f"{rel}: README is empty or a placeholder")
            for match in LINK.finditer(text):
                url = match.group(1) or match.group(2)
                if url.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = os.path.normpath(os.path.join(root, url.split("#")[0].split("?")[0]))
                if not os.path.exists(target):
                    errors.append(f"{rel}: broken link to {url}")

for error in sorted(set(errors)):
    print(f"::error::{error}")
print(f"{len(set(errors))} problem(s) found")
sys.exit(1 if errors else 0)
