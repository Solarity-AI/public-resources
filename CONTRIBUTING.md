# Contributing

This repository holds Solarity AI's **official, approved public materials**. It isn't a place for drafts or experiments.

## Outside contributors

If you find something wrong, outdated, or broken, [open an issue](https://github.com/Solarity-AI/public-resources/issues/new/choose). We don't accept outside pull requests that change brand or company content.

## Team members

### What belongs here

| Included | Not included |
| --- | --- |
| Approved brand assets and press materials | Source code or internal tooling |
| One-pagers and investor materials marked public | Confidential or NDA-protected documents |
| Careers information | Drafts or unapproved materials |
| Links to public policies | Internal strategy, or financials not explicitly marked public |

If you're unsure whether something belongs here, ask before adding it.

### Source of truth

[solarityai.com](https://solarityai.com/) is the source of truth.

- Every fact here (descriptions, dates, team, products, prices, contacts) must match the website.
- When the website changes, update this repository in the same week.
- Don't add numbers, user counts, or results that aren't published on the website.
- Link to policies on the website rather than copying them.

### How to make a change

1. Create a branch: `type/short-description`, for example `brand/add-svg-logo` or `careers/update-roles`.
2. Make the change and follow the rules below.
3. Run the checks locally: `python scripts/check.py`. On Windows, use `py -3.12 scripts/check.py` if `python` isn't found. This runs exactly what CI runs: Markdown lint, plus `scripts/check_docs.py`, which checks links, file names, file sizes, and empty READMEs. You need Node.js 22 (`.nvmrc`) for `npx` and Python 3.12 (`.python-version`).
4. Add a line to [CHANGELOG.md](CHANGELOG.md).
5. Open a pull request using the template. The **Docs check** workflow must pass, and a code owner must approve the PR before it is merged into `main`.

Use clear commit messages, such as `Add 512px sun mark export`. Avoid messages like "Add files via upload".

### File rules

- **Names:** use lowercase kebab-case with no spaces. Example: `solarity-sun-mark-512.png`, not `Solarity AI - Logo.png`.
- **Size:** keep web images under about 500 KB. Put print-resolution masters in a [GitHub Release](https://github.com/Solarity-AI/public-resources/releases), not in the repository.
- **Formats:** PNG for logos and icons (transparent), JPEG or WebP for photos, PDF for documents, SVG for vector logos.
- **Every folder** has a `README.md` that lists its files and how to use them.
- **Placeholders:** don't add empty folders or empty READMEs. Every README should say something useful, even if it's "None published yet."

### Regenerating images

Exports, banners, thumbnails, the type specimen, and the color swatches are generated from the masters. Don't edit them by hand.

```sh
pip install -r requirements.txt
python scripts/generate_assets.py
```

The script downloads Newsreader and Manrope once, from a pinned Google Fonts commit, into `.cache/fonts/`. To change a color, the navy glow, or a banner layout, edit the script, re-run it, and commit the images it changes.

### Cutting a release

1. Merge all changes to `main` and make sure the Docs check passes.
2. Build the kit: `python scripts/build_press_kit.py <version>`, for example `2026.11`. This writes `dist/solarity-ai-brand-and-press-kit-<version>.zip` and its `.sha256` checksum file.
3. Add a `CHANGELOG.md` entry for the release.
4. Publish it with the founder's approval: `gh release create brand-press-kit-<version> dist/solarity-ai-brand-and-press-kit-<version>.zip dist/solarity-ai-brand-and-press-kit-<version>.zip.sha256 --latest --title "Brand and press kit, <Month Year>"`, and quote the SHA-256 in the release notes.

### Standards

- [Pitch deck standards](docs/standards/pitch-decks.md)
- [One-pager standards](docs/standards/one-pagers.md)
- [Brand guidelines](brand/brand-guidelines/)

By contributing, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
