"""Build the brand and press kit ZIP attached to each GitHub release.

Run from the repository root: python scripts/build_press_kit.py <version>
Example: python scripts/build_press_kit.py 2026.10 → dist/solarity-ai-brand-and-press-kit-2026.10.zip
"""
import glob
import os
import sys
import zipfile

PATTERNS = [
    "brand/logos/*.png", "brand/banner/*.png", "brand/typography/*.png", "brand/social-media/*.jpg",
    "brand/colors/swatches/*.png", "press-kit/images/*.jpg", "press-kit/images/app-icons/*.png",
    "press-kit/images/screens/*.jpg",
]

README = """Solarity AI brand and press kit, {version}
=============================================

Source: https://github.com/Solarity-AI/public-resources (mirrors https://solarityai.com/press/)

1 line
Solarity AI builds AI self-improvement apps and the tools that let its small team ship them fast.

Short
Solarity AI LLC, based in Dallas, Texas, builds AI-powered self-improvement apps: Looks Max, IQ Max, Sleep Max, and Fitness Max (listed in the app stores as Only Fitness), all on iOS and Android. Building them shaped 3 SaaS products for teams that build mobile apps: Engineering Max, Management Max, and Marketing Max. Founder: Ata Turhan.

Using the name and images
- Write the name as Solarity AI: two words, with "AI" in capitals.
- Use the sun mark as supplied. Don't recolor, stretch, or redraw it.
- Fitness Max appears in the app stores as Only Fitness; name both when you link to its listing.
- Describe products with the facts on solarityai.com. Ask before stating numbers, users, or results.

Logo background: navy glow, #1F225C (center) to #0D1120 (edges).
Website colors: Night #0F0D0B, Cream #F5F1E8, Stone #C9C0B2, Gold #E9B56A. Fonts: Newsreader (headings), Manrope (body).
License: see https://github.com/Solarity-AI/public-resources/blob/main/LICENSE.md
Contact: ata.turhan@solarityai.com
"""


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/build_press_kit.py <version>   (for example 2026.10)")
    version = sys.argv[1]
    files = [f for pat in PATTERNS for f in sorted(glob.glob(pat))]
    if not files:
        sys.exit("No assets found. Run this from the repository root.")
    os.makedirs("dist", exist_ok=True)
    out = os.path.join("dist", f"solarity-ai-brand-and-press-kit-{version}.zip")
    root = "solarity-ai-brand-and-press-kit"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{root}/README.txt", README.format(version=version))
        for f in files:
            z.write(f, f"{root}/" + f.replace(os.sep, "/"))
    print(f"{out}: {len(files)} files + README.txt, {os.path.getsize(out) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
