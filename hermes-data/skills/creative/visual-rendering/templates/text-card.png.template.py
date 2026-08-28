"""text-card.png.template.py — minimal drop-in template for the recipe in SKILL.md.

Usage:
    /opt/hermes/.venv/bin/python text-card.png.template.py

Edit CONTENT below, then run. Produces /tmp/text-card.png.
"""
from PIL import Image, ImageDraw, ImageFont
import textwrap
from pathlib import Path

# ---- CONTENT (edit me) ---------------------------------------------------
TITLE    = "Title here"
SUBTITLE = "Subtitle / subject here"
PILL     = "STATUS PILL"   # or "" to omit
META_ROWS = [
    ("Label 1:", "value 1"),
    ("Label 2:", "value 2"),
    ("Label 3:", "value 3"),
]
BODY = """
Put the body text here. Multi-line is fine — keep it plain text or
a monospace-friendly transcript. Long lines will be wrapped to ~92
chars at 13px on a 1100px-wide image.
""".strip()
OUTPUT = "/tmp/text-card.png"

# ---- FONTS --------------------------------------------------------------
def load(size, mono=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf" if mono else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf" if mono else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        try: return ImageFont.truetype(p, size)
        except Exception: continue
    return ImageFont.load_default()

f_title, f_sub = load(20), load(14)
f_meta, f_pill = load(13), load(11)
f_body         = load(13, mono=True)

# ---- COLORS -------------------------------------------------------------
BG, CARD, BORDER = (244, 246, 248), (255, 255, 255), (229, 231, 235)
HDR_BG, HDR_BORDER, HDR_TITLE = (254, 226, 226), (254, 202, 202), (153, 27, 27)
META_BG, META_K, META_V       = (249, 250, 251), (107, 114, 128), (17, 24, 39)
BODY_COLOR = (17, 24, 39)

# ---- LAYOUT -------------------------------------------------------------
W, MARGIN, PAD = 1100, 24, 24
WRAP = 92

body_lines = []
for raw in BODY.split("\n"):
    body_lines.extend(textwrap.wrap(raw, width=WRAP) if raw else [""])
body_h   = len(body_lines) * 20
hdr_h    = 70
meta_h   = len(META_ROWS) * 22 + 24
H        = MARGIN + hdr_h + meta_h + 8 + body_h + 24 + MARGIN

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
x0, y0, x1, y1 = MARGIN, MARGIN, W - MARGIN, H - MARGIN
d.rounded_rectangle((x0, y0, x1, y1), radius=12, fill=CARD, outline=BORDER, width=1)

# Header
d.rounded_rectangle((x0, y0, x1, y0 + hdr_h), radius=12, fill=HDR_BG)
d.rectangle((x0, y0 + hdr_h - 12, x1, y0 + hdr_h), fill=HDR_BG)
d.line((x0, y0 + hdr_h, x1, y0 + hdr_h), fill=HDR_BORDER, width=1)
d.text((x0 + PAD, y0 + 16), TITLE, font=f_title, fill=HDR_TITLE)
if PILL:
    pb = d.textbbox((0, 0), PILL, font=f_pill)
    pw, ph = pb[2] - pb[0] + 16, pb[3] - pb[1] + 8
    d.rounded_rectangle((x1 - PAD - pw, y0 + 16, x1 - PAD, y0 + 16 + ph),
                        radius=999, fill=(254, 242, 242), outline=HDR_BORDER)
    d.text((x1 - PAD - pw + 8, y0 + 16 + 4), PILL, font=f_pill, fill=HDR_TITLE)
d.text((x0 + PAD, y0 + 16 + 28), SUBTITLE, font=f_sub, fill=(127, 29, 29))

# Meta
my = y0 + hdr_h
d.rectangle((x0, my, x1, my + meta_h), fill=META_BG)
d.line((x0, my + meta_h, x1, my + meta_h), fill=BORDER, width=1)
for i, (k, v) in enumerate(META_ROWS):
    ry = my + 12 + i * 22
    d.text((x0 + PAD, ry), k, font=f_meta, fill=META_K)
    d.text((x0 + PAD + 90, ry), v, font=f_meta, fill=META_V)

# Body
by = my + meta_h + 8
for i, line in enumerate(body_lines):
    d.text((x0 + PAD, by + i * 20), line, font=f_body, fill=BODY_COLOR)

Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
img.save(OUTPUT, "PNG", optimize=True)
print(f"wrote {OUTPUT} ({img.size[0]}x{img.size[1]})")
