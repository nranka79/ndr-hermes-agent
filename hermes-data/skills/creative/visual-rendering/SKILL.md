---
name: visual-rendering
description: "Render text/email/document content as a clean PNG image using Python PIL, with no browser engine required. Use when the user asks for a 'snapshot', 'screenshot', 'image of', or 'render of' an email, error message, or any text content — and especially when browser tools (camofox/Firecrawl) are unavailable."
version: 0.1.0
author: Hermes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [PIL, Pillow, PNG, image-rendering, email-snapshot, screenshot, browser-fallback]
---

# Visual Rendering (text → PNG, no browser)

Render any text content (email, error transcript, report, code block,
meeting summary) as a clean PNG image using only Python PIL. Designed as a
**browser-free fallback** for "send me a screenshot of X" requests when
`web_search`, `web_extract`, `browser_navigate`, or `browser_vision` are
unavailable or when the content isn't on a live URL (e.g. an email body,
a captured terminal output, a `git status` you want to share).

## When to use this

- User says "give me a snapshot / screenshot / image of [this content]"
- User says "render this as an image" or "send me a picture of [this]"
- You have a piece of text (email, code, error) you want to display
  natively in Telegram (which doesn't render text well above 4k chars
  or maintain visual structure)
- The browser stack is down (camofox daemon offline, Firecrawl
  unconfigured) and `vision_analyze` won't help because there is no
  live URL to navigate to

## When NOT to use this

- The content IS a live webpage with interactive elements (forms,
  dropdowns, JS-rendered state) — use `browser_vision` with a
  screenshot instead.
- The content is a code block that the user can just read inline — a
  raw text response is better than an image.
- The user wants an actual screenshot of THEIR screen — out of scope
  (this is for synthetic rendering, not OS-level screen capture).
- The user wants vector output (SVG) — use `creative/architecture-diagram`
  or `creative/excalidraw` instead.

## Recipe (copy-paste)

```python
from PIL import Image, ImageDraw, ImageFont
import textwrap, html as htmlmod

# --- Content ---------------------------------------------------------------
title  = "Bounce-back — Delivery failed"
subtitle = "Returned mail: see transcript for details"
body   = "<multi-line text exactly as you want it rendered>"

meta_rows = [
    ("From:", "Mail Delivery Subsystem <MAILER-DAEMON@host>"),
    ("To:",   "ndr@draas.com"),
    ("Date:", "Sat, 11 Jul 2026 17:48:47 GMT"),
]
pill_text = "PERMANENT FAILURE"   # or None to omit

# --- Fonts ----------------------------------------------------------------
def load(size, mono=False):
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf" if mono else
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf" if mono else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:    return ImageFont.truetype(path, size)
        except Exception: continue
    return ImageFont.load_default()

f_title = load(20);  f_sub = load(14);  f_meta = load(13)
f_body  = load(13, mono=True);  f_pill = load(11)

# --- Colors (Tailwind-ish gray/red palette) -------------------------------
BG, CARD, BORDER = (244, 246, 248), (255, 255, 255), (229, 231, 235)
HDR_BG, HDR_BORDER, HDR_TITLE, HDR_SUB = (254, 226, 226), (254, 202, 202), (153, 27, 27), (127, 29, 29)
META_BG, META_K, META_V = (249, 250, 251), (107, 114, 128), (17, 24, 39)

# --- Layout ----------------------------------------------------------------
W, margin, pad = 1100, 24, 24

# Wrap body at ~92 chars (works for monospace 13px at 1100px wide)
body_lines = []
for raw in body.split("\n"):
    wrapped = textwrap.wrap(raw, width=92) if raw else [""]
    body_lines.extend(wrapped)
body_h = len(body_lines) * 20

# Header and meta heights
hdr_h = 70
meta_h = len(meta_rows) * 22 + 24   # 12px top + rows + 12px bottom

# Total card height
H = margin + hdr_h + meta_h + 8 + body_h + 24 + margin
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# Card outline
x0, y0, x1, y1 = margin, margin, W - margin, H - margin
d.rounded_rectangle((x0, y0, x1, y1), radius=12, fill=CARD, outline=BORDER, width=1)

# Header
d.rounded_rectangle((x0, y0, x1, y0 + hdr_h), radius=12, fill=HDR_BG)
d.rectangle((x0, y0 + hdr_h - 12, x1, y0 + hdr_h), fill=HDR_BG)
d.line((x0, y0 + hdr_h, x1, y0 + hdr_h), fill=HDR_BORDER, width=1)
d.text((x0 + pad, y0 + 16), title, font=f_title, fill=HDR_TITLE)

if pill_text:
    pb = d.textbbox((0, 0), pill_text, font=f_pill)
    pw, ph = pb[2] - pb[0] + 16, pb[3] - pb[1] + 8
    d.rounded_rectangle((x1 - pad - pw, y0 + 16, x1 - pad, y0 + 16 + ph),
                        radius=999, fill=(254, 242, 242), outline=HDR_BORDER)
    d.text((x1 - pad - pw + 8, y0 + 16 + 4), pill_text, font=f_pill, fill=HDR_TITLE)

d.text((x0 + pad, y0 + 16 + 28), subtitle, font=f_sub, fill=HDR_SUB)

# Meta block
my = y0 + hdr_h
d.rectangle((x0, my, x1, my + meta_h), fill=META_BG)
d.line((x0, my + meta_h, x1, my + meta_h), fill=BORDER, width=1)
for i, (k, v) in enumerate(meta_rows):
    ry = my + 12 + i * 22
    d.text((x0 + pad, ry), k, font=f_meta, fill=META_K)
    d.text((x0 + pad + 90, ry), v, font=f_meta, fill=META_V)

# Body
by = my + meta_h + 8
for i, line in enumerate(body_lines):
    d.text((x0 + pad, by + i * 20), line, font=f_body, fill=(17, 24, 39))

# Save
img.save("/tmp/render.png", "PNG", optimize=True)
```

## Adapting the recipe for other content types

The four-block layout (header → meta → body → save) is the workhorse. To
adapt:

| Content | Header | Meta rows | Body |
|---|---|---|---|
| Email | "Email — [Subject]" + pill for status (Bounced/Sent) | From/To/Date/Account | raw email body |
| Code/Error | "Error — [error class]" + pill for severity (FATAL/WARN) | File/Line/Tool | stack trace or code |
| Report | "Report — [title]" | Period/Author/Source | markdown body |
| Meeting | "Meeting — [date]" | Time/Attendees/Location | agenda or summary |
| Git status | "Git status — [branch]" | Repo/HEAD/Clean? | full `git status` output |

## Pitfalls

### 1. Always verify the rendered image with `vision_analyze` afterward

PIL silently truncates text that overflows the image bounds — no exception
is raised. After saving, run `vision_analyze(image_url="/tmp/render.png",
question="is the recipient X visible? is the title not clipped?")` to
confirm the key text actually appears in the output. The OCR pass returns
extracted text directly (free, no model call) when the image contains
readable text, so this is cheap.

### 2. Monospace font for code/email bodies, sans-serif for labels

If the body is monospace content (terminal output, email plaintext,
stack trace, code), force a monospace font (`DejaVuSansMono`) and use
`textwrap.wrap(raw, width=N)` where N is calibrated to the chosen font
size (~92 chars at 13px on a 1100px-wide image is a safe starting point).
Mixing monospace body with sans-serif headers and meta gives the cleanest
"email client" / "report" look.

### 3. `rounded_rectangle` corner-clipping for full-width bars

When you draw a header or meta bar that spans the full card width, the
rounded corners of the card are inside the bar. Fix by:
1. Drawing the bar as a `rounded_rectangle` with the same `radius=12`
2. Then drawing a flat `rectangle` over the bottom 12px of the bar to
   square off the bottom edge
3. Drawing the bar's bottom border as a `line` instead of a rect

Otherwise the bar's bottom corners poke out of the card's rounded corners.

### 4. The 24px `margin` outside the card is the Telegram "frame"

Telegram displays images without padding. If you want the image to look
like a card (with white space around it), the `margin=24` of background
color around the card is essential. If you remove it, the card's rounded
corners will appear right at the image edge.

### 5. Pill text measurement: `textbbox`, not `textsize`

`ImageDraw.textsize()` was deprecated in Pillow 10. Use:

```python
left, top, right, bottom = d.textbbox((0, 0), text, font=font)
width, height = right - left, bottom - top
```

`textbbox` returns absolute coordinates, so subtract `(left, top)` if you
need the visual width (most cases).

### 6. Telegram-native delivery

To deliver the image, use `MEDIA:/tmp/render.png` in your reply — the
Telegram channel automatically delivers it as a native photo. Do NOT
base64-embed the image in your reply or paste the path; use the
`MEDIA:<path>` convention.

### 7. When to use a different tool

- Live webpage → `browser_navigate` then `browser_vision`
- Code block ≤100 lines → just paste as text
- PDF page → `vision_analyze` with the PDF path, or `ocr-and-documents` to
  extract text first
- Animated content → out of scope (this recipe is for static snapshots)

## Templates

- `templates/text-card.png.template.py` — drop-in starter script. Edit the
  CONTENT block at the top, run with the active venv's Python
  (`/opt/hermes/.venv/bin/python ...`), and the rendered PNG lands in
  `/tmp/text-card.png`. Useful for one-off content rendering where you
  don't need to write the full script from scratch.

## Verification

After producing the image, before reporting success to the user:

1. Save to `/tmp/render.png`.
2. Call `vision_analyze(image_url="/tmp/render.png", question="is the
   [key field] visible? is anything clipped?")`. The OCR pass will
   surface any text that overflowed.
3. If you changed widths or font sizes, re-measure with a 1-2 line test
   body first to confirm character-wrap width before rendering the full
   content.
