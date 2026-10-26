# Changelog

Notable changes to Solarity AI's public resources.

## 2026-10-26

### Added

- README: a "Start here" line, the intended audience, a row of app icons, a brand guidelines row in the quick downloads, and a changelog link
- A footer on every sub-page linking back to all resources and to a contact
- Previews on the asset pages: the sun mark on the logos page, both banners, a Newsreader and Manrope type specimen, the share image, and founder and screen thumbnails in the press images page
- 300 px screen thumbnails (`press-kit/images/screens/thumbs/`)
- Logo navy documented in `brand/colors/` and the brand guidelines
- Developer tooling: `scripts/check.py` (everything CI runs, on any OS), `scripts/generate_assets.py` (regenerates every derived image from the masters), `scripts/build_press_kit.py` (release ZIP with `.sha256`), tests for all three in `tests/`, and CONTRIBUTING sections on running checks, regenerating images, and cutting a release
- Version pins (`.nvmrc`, `.python-version`, `requirements.txt`), `.editorconfig`, `.gitignore`, VS Code recommendations, and `CLAUDE.md` for AI agents

### Changed

- The founder's title is "Founder" everywhere (founder's request); "Founder & CEO" is removed
- The sun mark, banners, and profile pictures sit on the navy glow from the original Solarity logo (`#1F225C` at the center to `#0D1120` at the edges), replacing the dark website background. `solarity-sun-mark-on-dark*.png` are replaced by `solarity-sun-mark-on-navy.png`, `-512`, and `-192`
- Wording: counts use digits as on solarityai.com, and Fitness Max is written one way, "Fitness Max (listed as Only Fitness)"
- Wording: links say what they open instead of showing repository paths, the careers apply line, remote benefit, and job posters link are clearer, "Ahead" is now "Planned", the demo page is titled "Try the products", the README title is sentence case, and the correction form hint moved into the field description
- The demos page no longer says every product can be tried live: the apps can be tried today, Management Max has a free plan, and Engineering Max and Marketing Max take access requests
- Design: app icons in tables set their height, so they no longer collapse on phones; the products and colors tables fit better at 375 px; the screenshots page uses 300 px thumbnails; the press kit page puts the ZIP download first
- Accessibility (WCAG 2.2 AA): store links share a list item with their app name, key–value tables have real headers, "Download" links fetch the file, link text matches destinations, screenshot alt text describes each screen, careers roles and the brand rules are real headings, founder profiles are a list, and the color swatches are marked decorative
- Links to solarityai.com pages carry `utm_source=github` campaign tags, because GitHub strips the referrer
- CI uses the pinned Python version and runs the script tests; `scripts/check.py` explains what to install when Node is missing, and the font download times out after 30 s with a clear message

### Security

- README and CONTRIBUTING describe the actual review model: required automated checks, and the founder as sole code owner
- Hardened the CI workflow and scripts: actions are pinned to commit SHAs, the checkout token isn't persisted, npx skips install scripts, downloaded fonts are verified against SHA-256 hashes, release ZIPs get a `.sha256` checksum, and Dependabot watches GitHub Actions and pip

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
