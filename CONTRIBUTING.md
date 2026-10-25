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
3. Open a pull request using the template. A code owner must approve it before it is merged into `main`.
4. Add a line to [CHANGELOG.md](CHANGELOG.md).

Use clear commit messages, such as `Add 512px sun mark export`. Avoid messages like "Add files via upload".

### File rules

- **Names:** use lowercase kebab-case with no spaces. Example: `solarity-sun-mark-512.png`, not `Solarity AI - Logo.png`.
- **Size:** keep web images under about 500 KB. Put print-resolution masters in a [GitHub Release](https://github.com/Solarity-AI/public-resources/releases), not in the repository.
- **Formats:** PNG for logos and icons (transparent), JPEG or WebP for photos, PDF for documents, SVG for vector logos.
- **Every folder** has a `README.md` that lists its files and how to use them.
- **Placeholders:** don't add empty folders or empty READMEs. Every README should say something useful, even if it's "None published yet."

### Standards

- [Pitch deck standards](docs/standards/pitch-decks.md)
- [One-pager standards](docs/standards/one-pagers.md)
- [Brand guidelines](brand/brand-guidelines/)

By contributing, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
