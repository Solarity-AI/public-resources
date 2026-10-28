"""Regenerate every derived image from the masters.

Run: python scripts/generate_assets.py   (from any folder; paths are relative to the repository root)
Needs Pillow (pip install -r requirements.txt). Fonts are downloaded once, from a pinned
google/fonts commit, into .cache/fonts/.

Masters (never generated): brand/logos/solarity-sun-mark.png, press-kit/images/app-icons/*.png,
press-kit/images/screens/*.jpg, press-kit/images/ata-turhan-founder.jpg.
"""
import glob
import hashlib
import math
import os
import sys
import urllib.request

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # checked when the script runs, so --help works without it
    Image = None

# (URL at a pinned google/fonts commit, expected SHA-256 of the file)
FONTS = {
    "Newsreader.ttf": ("https://raw.githubusercontent.com/google/fonts/991ce1de6075188e6b8977a5aa9fcd3610a4e946/ofl/newsreader/Newsreader%5Bopsz,wght%5D.ttf",
                       "8a08d13f8a6c0d51be379a60af84f945f65369a67e509ee3c3bdcc421254d7c1"),
    "Manrope.ttf": ("https://raw.githubusercontent.com/google/fonts/b31870aff700ab7a1d74fa0c6887d95beb9e0037/ofl/manrope/Manrope%5Bwght%5D.ttf",
                    "3ae11c49db0455a3cc33e37d380f20fdb8c7f8b41dc07625c177e3d87a9d6ae6"),
}
FONT_DIR = os.path.join(".cache", "fonts")

# Website palette (brand/colors)
NIGHT = (15, 13, 11)
CREAM = (245, 241, 232)
STONE = (201, 192, 178)
GOLD = (233, 181, 106)
TAUPE = (169, 159, 145)
UMBER = (42, 35, 28)
SWATCHES = {
    "night": "0F0D0B", "cream": "F5F1E8", "stone": "C9C0B2", "gold": "E9B56A", "light-gold": "FFCF7A",
    "sand": "D6BF9A", "taupe": "A99F91", "bronze": "9C7446", "umber": "2A231C", "ember": "1A140E",
    "navy": "1F225C", "navy-deep": "0D1120", "sun-yellow": "FFCD07",
}

# Logo navy: radial profile sampled from the original Solarity logo (centre → edge)
NAVY_STOPS = [(0.00, (0x1F, 0x22, 0x5C)), (0.14, (0x1D, 0x20, 0x58)), (0.29, (0x19, 0x19, 0x4E)),
              (0.43, (0x0F, 0x11, 0x40)), (0.57, (0x0C, 0x11, 0x30)), (0.71, (0x0F, 0x10, 0x2A)),
              (0.86, (0x0D, 0x11, 0x20)), (1.00, (0x0D, 0x10, 0x1C))]


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def fetch_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    for name, (url, digest) in FONTS.items():
        path = os.path.join(FONT_DIR, name)
        if not os.path.exists(path):
            print(f"Downloading {name}")
            try:
                with urllib.request.urlopen(url, timeout=30) as r, open(path + ".part", "wb") as f:
                    f.write(r.read())
            except OSError as e:
                if os.path.exists(path + ".part"):
                    os.remove(path + ".part")
                raise SystemExit(f"Couldn't download {name} ({e}). Check your connection, or save {url} as {path} and run again.")
            os.replace(path + ".part", path)
        if sha256(path) != digest:
            os.remove(path)
            raise SystemExit(f"{name}: SHA-256 mismatch, file deleted. Refusing to use an unverified font.")


def font(name, size, weight):
    f = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    vals = []
    for a in f.get_variation_axes():
        n = a.get("name", b"")
        n = n.decode() if isinstance(n, bytes) else str(n)
        vals.append(weight if "eight" in n else min(max(size * 0.75, a["minimum"]), a["maximum"]))
    f.set_variation_by_axes(vals)
    return f


def navy_color(d):
    d = min(d, 1.0)
    for (a, ca), (b, cb) in zip(NAVY_STOPS, NAVY_STOPS[1:]):
        if d <= b:
            t = (d - a) / (b - a)
            return tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))
    return NAVY_STOPS[-1][1]


def navy(w, h, cx, cy, rx, ry):
    s = 4
    sw, sh = max(1, w // s), max(1, h // s)
    img = Image.new("RGB", (sw, sh))
    px = img.load()
    for y in range(sh):
        for x in range(sw):
            px[x, y] = navy_color(math.hypot((x * s - cx) / rx, (y * s - cy) / ry))
    return img.resize((w, h), Image.BICUBIC)


def save(img, path, **kw):
    img.save(path, optimize=True, **kw)
    print("wrote", path)


def logos(mark):
    for w in (512, 256, 192, 64):
        save(mark.resize((w, round(mark.height * w / mark.width)), Image.LANCZOS), f"brand/logos/solarity-sun-mark-{w}.png")
    size = 1200
    # Radii tuned so the mean background matches the original logo's RGB (23, 24, 69)
    bg = navy(size, size, size / 2, size / 2, size * 1.3, size * 0.95).convert("RGBA")
    w = int(size * 0.66)
    m = mark.resize((w, round(mark.height * w / mark.width)), Image.LANCZOS)
    bg.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
    on_navy = bg.convert("RGB")
    save(on_navy, "brand/logos/solarity-sun-mark-on-navy.png")
    for s in (512, 192):
        save(on_navy.resize((s, s), Image.LANCZOS), f"brand/logos/solarity-sun-mark-on-navy-{s}.png")


def banner(mark, W, H):
    img = navy(W, H, W * 0.42, H / 2, W * 0.95, H * 1.2).convert("RGBA")
    ms = int(H * 0.56)
    mm = mark.resize((ms, round(mark.height * ms / mark.width)), Image.LANCZOS)
    img.alpha_composite(mm, (int(W * 0.24) - mm.width // 2, H // 2 - mm.height // 2))
    d = ImageDraw.Draw(img)
    x = int(W * 0.44)
    d.text((x, int(H * 0.27)), "Solarity AI", font=font("Newsreader.ttf", int(H * 0.19), 500), fill=CREAM)
    d.text((x, int(H * 0.53)), "Building for human potential.", font=font("Manrope.ttf", int(H * 0.058), 500), fill=STONE)
    d.text((x, int(H * 0.68)), "SOLARITYAI.COM", font=font("Manrope.ttf", int(H * 0.042), 600), fill=GOLD)
    save(img.convert("RGB"), f"brand/banner/solarity-ai-banner-{W}x{H}.png")


def specimen():
    W, H = 1280, 600
    im = Image.new("RGB", (W, H), NIGHT)
    d = ImageDraw.Draw(im)
    d.text((64, 52), "NEWSREADER  ·  DISPLAY AND HEADINGS", font=font("Manrope.ttf", 20, 700), fill=GOLD)
    d.text((64, 92), "Building for human potential.", font=font("Newsreader.ttf", 76, 500), fill=CREAM)
    d.text((64, 196), "Aa Bb Cc  0123456789", font=font("Newsreader.ttf", 44, 400), fill=STONE)
    d.line((64, 282, W - 64, 282), fill=UMBER, width=2)
    d.text((64, 318), "MANROPE  ·  BODY, INTERFACE, AND LABELS", font=font("Manrope.ttf", 20, 700), fill=GOLD)
    d.text((64, 358), "Solarity AI builds AI self-improvement apps and the tools", font=font("Manrope.ttf", 34, 500), fill=CREAM)
    d.text((64, 404), "that let its small team ship them fast.", font=font("Manrope.ttf", 34, 500), fill=CREAM)
    x = 64
    for wt, lab in ((400, "Regular 400"), (500, "Medium 500"), (600, "SemiBold 600"), (700, "Bold 700")):
        d.text((x, 478), "Aa", font=font("Manrope.ttf", 34, wt), fill=STONE)
        d.text((x, 526), lab, font=font("Manrope.ttf", 18, 500), fill=TAUPE)
        x += 280
    save(im, "brand/typography/solarity-ai-type-specimen.png")


def swatches():
    for name, hexv in SWATCHES.items():
        c = tuple(int(hexv[i:i + 2], 16) for i in (0, 2, 4))
        im = Image.new("RGB", (48, 48), (136, 135, 128))
        ImageDraw.Draw(im).rectangle((2, 2, 45, 45), fill=c)
        save(im, f"brand/colors/swatches/{name}.png")


def thumbnails():
    for p in sorted(glob.glob("press-kit/images/app-icons/*-icon.png")):
        out = os.path.join("press-kit/images/app-icons/thumbs", os.path.basename(p).replace(".png", "-96.png"))
        save(Image.open(p).convert("RGBA").resize((96, 96), Image.LANCZOS), out)
    for p in sorted(glob.glob("press-kit/images/screens/*.jpg")):
        im = Image.open(p).convert("RGB")
        out = os.path.join("press-kit/images/screens/thumbs", os.path.basename(p).replace(".jpg", "-300.jpg"))
        save(im.resize((300, round(im.height * 300 / im.width)), Image.LANCZOS), out, quality=82, progressive=True)
    # Pages show the founder photo at 120-200 px; 400 px covers 2x screens at a fifth of the master's bytes
    os.makedirs("press-kit/images/thumbs", exist_ok=True)
    im = Image.open("press-kit/images/ata-turhan-founder.jpg").convert("RGB")
    save(im.resize((400, 400), Image.LANCZOS), "press-kit/images/thumbs/ata-turhan-founder-400.jpg", quality=82, progressive=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:  # no options: -h, --help, or anything else prints this instead of rewriting the images
        print(__doc__)
        sys.exit(0 if sys.argv[1] in ("-h", "--help") else 2)
    if Image is None:
        sys.exit("generate_assets.py needs Pillow. Run: pip install -r requirements.txt")
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # every path below is repo-relative
    fetch_fonts()
    mark = Image.open("brand/logos/solarity-sun-mark.png").convert("RGBA")
    logos(mark)
    banner(mark, 1280, 640)
    banner(mark, 1500, 500)
    specimen()
    swatches()
    thumbnails()
