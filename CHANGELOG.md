# Changelog

Notable changes to Solarity AI's public resources.

## 2026-10-28

### Changed

- The founder bio and press images pages show a 400 px preview of the founder photo (20 KB instead of the 94 KB master, which they still link to), built by `scripts/generate_assets.py` into `press-kit/images/thumbs/` (#145)
- Every image sets both width and height, so pages don't shift while images load: the README banner, the company one-pager logo, and the founder photo gained a height, and a test checks it (#146)
- The script tests are split into one module per script, with shared helpers in `tests/support.py`; `scripts/check_docs.py` runs its checks from functions instead of top-level code; and `scripts/generate_assets.py` takes its drawing colors from the palette table (#149, #150, #151, #152, #153)
- README, CONTRIBUTING, SECURITY, and `CLAUDE.md` match the scripts and tests again: every image needs width and height, the docs check fails files over 1 MB (aim for 500 KB), the repository holds a few check and build scripts, and the README lists `tests/` (#155)
- The size rule is one rule everywhere: the docs check fails any file over 1 MB, and about 500 KB is guidance for images a page displays, not for downloadable masters. CLAUDE.md, CONTRIBUTING, and the pull request template say so (#157)

### Fixed

- `scripts/check_docs.py` fails a solarityai.com link that lacks `utm_medium=public-resources` or a campaign, or that misspells a tag's name; it used to check only for `utm_source=github` (#126)
- File-name links in tables are plain links instead of code, so they meet WCAG's 4.5:1 contrast in GitHub's striped table rows (they measured 4.34:1) (#160)
- `docs/` has a README, and `scripts/check_docs.py` now requires one in folders that only hold other folders (#161)
- The privacy summary no longer says Solarity AI receives only what you choose to send; like the policy, it mentions the IP address and browser type Cloudflare handles on every visit (#162)
- The colors page uses the website's names: `#1A140E` is Ink (text on Light gold buttons), Ember is `#D9782F`, Raised `#221C16` is the raised-surface color, and Light gold is for primary buttons and focus. `ember.png` now shows the website's Ember; `ink.png` and `raised.png` are new (#129)
- `scripts/check_docs.py` catches untagged website links written with http, a bare `www.` address, capitals, or punctuation after the address (#163); applies the 1 MB limit to every file (#164); treats `~~~` and longer fences as code (#165); finds the anchors of setext, indented, and emphasized headings (#166); accepts `//host` and percent-encoded links (#167); and no longer counts `kit.zip` as listed when only `kit.zip.sha256` is (#168)
- `scripts/build_press_kit.py --help` prints its usage and exits 0, like the other scripts (#169)

## 2026-10-27

### Added

- Tests for `scripts/check.py` (a failed step fails CI, and a missing Node.js says what to install), the font download failure path, thumbnails, the logo navy background, the press kit ZIP contents, and the size and folder-name rules of `scripts/check_docs.py` (#107, #109, #110, #113, #114, #116)
- `tests/test_content.py` guards brand rules: the title is Founder, Solarity AI is two words, Only Fitness always appears with Fitness Max, swatches match their documented colors, every master image has a thumbnail, and table images set width and height (#108, #111, #112, #113, #115)

### Changed

- Pull requests no longer need an approving review: the **Docs check** must pass, and only the founder can merge. README, CONTRIBUTING, CODEOWNERS, and `CLAUDE.md` say so (#104)
- Markdown lint runs markdownlint-cli2 0.23.3 instead of 0.18.1, whose line had no release since May 2025 (#119)
- markdownlint-cli2 is installed from `package.json` and `package-lock.json` (run `npm ci` once), so its dependencies are locked and Dependabot proposes its updates, at least 7 days after each release (#120)

### Security

- markdownlint-cli2 0.24.0, plus a `katex` override to 0.18.11, clears the 6 `npm audit` advisories in the linter's dependencies (markdown-it, smol-toml, katex). They only affected how the linter parses this repository's own Markdown (#124)

### Fixed

- `scripts/check.py` says to run `npm ci` again when `node_modules` no longer matches `package-lock.json`, instead of linting with the old version (#131)
- `scripts/check_docs.py` reads file names and prints messages with any characters on Windows (#132), counts a file as listed only by its whole name or a link to it (#133), checks links with `'title'` and `(title)` (#134), ignores link syntax inside code (#135), accepts links that start with `/` (#136), and answers `--help` and a missing folder with a message instead of a traceback (#137)
- `scripts/generate_assets.py` prints its usage for `--help` instead of rewriting every image (#137) and says to install `requirements.txt` when Pillow is missing (#138); `scripts/build_press_kit.py` rejects versions written with non-ASCII digits (#139)
- The careers page describes the remote benefit in the website's words (#130), the screenshots page says the Engineering Max screen is its scan of Sleep Max (#140), and the default share image's alt text names the Solarity AI wordmark it shows (#141)

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

### Fixed

- The release ZIP is byte-for-byte reproducible: the same files give the same SHA-256 on any checkout (#82)
- `scripts/check_docs.py` checks the repository wherever it is run from, skips anything `.gitignore` excludes (such as a local `.venv/`), and now also requires a README in every folder, flags decorative images that GitHub would turn into unnamed links, and flags solarityai.com page links without campaign tags (#83, #85, #84, #88, #89)
- `scripts/generate_assets.py` works from any folder instead of downloading fonts into the wrong place and crashing (#86); `scripts/build_press_kit.py` accepts only versions like `2026.10` (#87)
- Swatches and app icon previews no longer become links with no name for screen readers (#84)
- READMEs for the swatch, app icon, and screen folders (#88), and campaign tags on the remaining solarityai.com page links (#89)
- The release ZIP gives the same SHA-256 on Windows, macOS, and Linux, not just on one machine (#92); `scripts/build_press_kit.py` rejects impossible months such as `2026.13` (#99)
- The privacy summary and legal index match the policy on solarityai.com: effective October 26, 2026, and careers applications go through FormSubmit after a Google reCAPTCHA check (#93)
- `scripts/check_docs.py` checks `href` links, links with titles, reference links, and `#anchors` (#94, #95); matches link case exactly, as GitHub does, on every OS (#96); reports a non-UTF-8 file instead of crashing (#98); accepts `<picture>` with `<source>` and catches `alt=''` (#100); catches untagged `https://solarityai.com` and `www.` links (#101); and requires each README to list its folder's files (#102)
- Markdown lint skips what `.gitignore` excludes, such as a local `.venv/` (#97)
- The thumbnail folder READMEs list their files (#102)

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
