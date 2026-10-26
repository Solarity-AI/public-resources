# Changelog

Notable changes to Solarity AI's public resources.

## 2026-10-26

### Changed

- Wording pass: counts use digits as on solarityai.com, and Fitness Max is written one way, "Fitness Max (listed as Only Fitness)"
- Quick-download and press image links say what they open instead of showing repository paths
- Clearer careers apply line, remote benefit, and job posters link
- "Ahead" is now "Planned" in the company one-pager, the demo page is titled "Try the products", and the README title is sentence case
- The correction form hint moved from the field label into its description
- The demos page no longer says every product can be tried live: the apps can be tried today, Management Max has a free plan, and Engineering Max and Marketing Max take access requests

## 2026-10-25

### Added

- A **Docs check** CI workflow (`.github/workflows/docs-check.yml`) running Markdown lint and `scripts/check_docs.py`, which checks links, file names, file sizes, and empty READMEs
- `.markdownlint-cli2.jsonc` with rules suited to this repository
- Sun mark exports on the dark background at 192 and 512 px, for light pages
- 96 px app icon thumbnails for embedding (`press-kit/images/app-icons/thumbs/`)
- Local color swatches (`brand/colors/swatches/`), which replace the third-party placeholder images

### Changed

- The company one-pager uses the sun mark on its dark background, so it keeps contrast in GitHub's light mode
- Press kit descriptions use real headings, and the README's "more" link now says "all channels"
- Fixed Markdown structure across the standards docs and the changelog

- Rewrote the founder bio from [ataturhan.com](https://ataturhan.com/): 1-line, short, and long bios, plus facts, education, achievements, speaking topics, contacts, and profiles
- Founder references now link to the bio and ataturhan.com, and the root README and company one-pager say "Founder & CEO"
- Added key app features from ataturhan.com/solarity-ai to the mobile apps one-pager
- Added the founder's profiles to `brand/social-media/`

## 2026-10-24

### Added

- Website-aligned content in every folder: brand colors, typography, social channels, guidelines, press kit, one-pagers, careers, demos, and public policies
- The official sun mark from the solarityai.com press kit, plus 512, 256, 192, and 64 px exports and a version on a dark background
- New banners (1280 × 640 and 1500 × 500) in the website style
- The official press images: founder photo, 4 app icons, and 7 product screens
- `LICENSE.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CODEOWNERS`, and issue and pull request templates

### Changed

- Rewrote the root README for external visitors
- Renamed `job-description/` to `careers/`, updated to the 2 roles currently listed on solarityai.com
- Moved the pitch deck and one-pager standards to `docs/standards/`
- Switched all file names to kebab-case

### Removed

- The navy "SOLARITY / ALWAYS BETTER" logo and banner, superseded by the sun mark
- The 6.3 MB founder PNG, replaced by the official 800 × 800 JPEG
- The hiring PDF, which listed 3 roles and an outdated link

Originals of the removed files are kept in the [`legacy-brand-2026.04`](https://github.com/Solarity-AI/public-resources/releases/tag/legacy-brand-2026.04) release.
