# Solarity AI public resources: instructions for AI agents

Official public materials for Solarity AI LLC: brand assets, press kit, founder bio, one-pagers, careers, and policy links. The repository holds Markdown and images only, with no app code.

## Sources of truth

- **Company facts:** [solarityai.com](https://solarityai.com/). Every description, date, team member, product, price, and contact must match it. When they disagree, the website wins.
- **Founder facts:** [ataturhan.com](https://ataturhan.com/) for `press-kit/founder-bio/`.
- Never invent numbers, users, results, testimonials, or claims. Link to policies on the website rather than copying them.

## Brand rules that are easy to regress

- **Logo background is navy, not the dark website color.** The sun mark, banners, and profile pictures sit on the navy glow from the original Solarity logo: `#1F225C` at the center to `#0D1120` at the edges. Files: `brand/logos/solarity-sun-mark-on-navy*.png`.
- Never recolor, stretch, or redraw the sun mark (`brand/logos/solarity-sun-mark.png` is the master).
- Ata Turhan's title is **Founder**. Never write "CEO" or "Founder & CEO" (founder's request, 2026-10-26).
- Write **Solarity AI** (two words). Write "Fitness Max (listed as Only Fitness)" inline.
- Counts use digits ("4 apps", "3 SaaS products"), as on the website.
- The website palette (Night `#0F0D0B`, Cream, Stone, Gold) and the fonts (Newsreader, Manrope) are documented in `brand/colors/` and `brand/typography/`.

## Conventions

- File and folder names are lowercase kebab-case. Images go up to 1 MB, and larger masters go in a GitHub Release.
- Every folder has a non-empty `README.md` ending with the "← All public resources · Questions?" footer.
- Images inside tables need both `width` and `height`, or GitHub collapses them on phones.
- Links from READMEs to solarityai.com pages carry `utm_source=github&utm_medium=public-resources&utm_campaign=<page>`.
- Accessibility: descriptive link text, real headers on tables, and alt text that describes the image (decorative images get `alt=""`).

## Commands

```sh
python scripts/check.py                    # everything CI runs (Markdown lint + docs checker)
pip install -r requirements.txt            # Pillow, for the two scripts below
python scripts/generate_assets.py          # regenerate exports, banners, thumbnails, specimen, swatches
python scripts/build_press_kit.py 2026.10  # build dist/ ZIP for a release
```

On Windows use `py -3.12` if `python` points elsewhere. Node 22 (`.nvmrc`) is needed for `npx`.

## Workflow

1. Branch, change, run `python scripts/check.py`, and add a line to `CHANGELOG.md`.
2. Open a PR. Commit messages and PR descriptions follow the session's attribution rules.
3. The owner has authorized admin squash-merging PRs right after opening them: `gh pr merge <n> --admin --squash`. Don't merge over a failing check.
4. Repository and organization settings, releases, and anything public outside the repository need the owner's explicit approval each time.
