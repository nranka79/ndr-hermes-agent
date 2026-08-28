# Project Specifications Presentation from Google Sheets

## When to Use

Generate a branded project specifications presentation from Google Sheets data when the user asks for project spec sheets, specification documents, or technical details about a real estate project — and they want it as a presentation (not a doc), using DRA brand colors and excluding investor/financial sections.

Trust this reference for Prakash (psingh@draas.com) sessions: he prefers branded presentations over docs, and wants only technical specs, amenities, and competitive positioning — no investor specs or financials.

## Source Data

Data is typically spread across 8-9 sheets in one workbook:

| Sheet | Content |
|-------|---------|
| Comp Data | Competitive project comparison (pricing, specs, RERA, developer) |
| P Line Value of the Comp Projects | Villa variants with room-by-room carpet areas, P Line loading |
| 2025NOV04 | Feature comparison with specific competitors |
| Complete Comparitive Analysis | Room-wise breakdown for multiple villa types |
| Specifications | Detailed spec comparison (row: category/subcategory, col: project) |
| Oasis Specs | Premium spec level for the subject project |
| Oasis investor specs | Lower spec level — exclude for specs-only presentation |
| Plots Data | Plot-only competitive data |
| Villa Dimension | Room dimension data across projects |

## Workflow

### Step 1 — Read Sheet Data

Use `terminal()` to call the Sheets API directly (not `execute_code` — the sandbox lacks `gws_fetch_token` stub):

```python
import os, sys
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.gws_auth import load_credentials
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = load_credentials("<telegram_id>", "google-draas")
service = build("sheets", "v4", credentials=creds)

result = service.spreadsheets().values().get(
    spreadsheetId="<SHEET_ID>",
    range="'SheetName'"
).execute()
```

**⚠️ `execute_code` sandbox limitation**: `GWS_VAULT_SOCKET` is NOT set in the sandbox, and `gws_fetch_token` is not in the generated `hermes_tools.py` stub. Always use `terminal()` context with explicit `GWS_VAULT_SOCKET` env var set. Calling `gws_skill_bridge.call()` or `gws_auth.build_service()` from within `execute_code` will fail with `ImportError: cannot import name 'gws_fetch_token'`.

Also: calling `gws_skill_bridge.call()` from nested `terminal()` calls inside `execute_code` also fails — the child process doesn't inherit the vault socket. Use `terminal()` at the top level (outside `execute_code`) with a standalone Python script that sets `os.environ['GWS_VAULT_SOCKET']` before importing.

### Step 2 — Structure the Presentation

18-slide structure for a specs-only deck (no investor/finance):

| Slide | Content |
|-------|---------|
| 1 | **Cover** — Full-bleed navy, gold corner accent, project name, location, CONFIDENTIAL |
| 2 | **Project Overview** — 6 metric cards + details table |
| 3 | **Villa Variants** — Configurations table (variant, BHK, plot, BU area, FSI, floors) |
| 4-6 | **Room-wise Breakdown** — Each major variant with carpet area cards |
| 7 | **Structural Specs** — RCC, ceiling height, foundation, waterproofing |
| 8 | **Joinery** — Doors, windows, railings, grills |
| 9 | **Flooring** — Room-by-room with brand references |
| 10 | **Painting & Finishes** — Paint specs, POP ceilings, geyser provision |
| 11 | **Bathroom Fittings** — Sanitary ware, faucets, accessories |
| 12 | **Kitchen** — Countertop, backsplash, utilities |
| 13 | **Electrical** — Wiring, backup, AC provision, point counts |
| 14 | **Plumbing** — Piping brands, tank capacities, water supply |
| 15 | **Security & Smart Home** — CCTV, intercom, smart locks, sensors |
| 16 | **Sustainability** — Solar, rainwater, STP, irrigation |
| 17 | **Amenities** — Clubhouse, pool, sports, community, wellness |
| 18 | **Competitive Positioning** — Key advantages vs comp set |

### Step 3 — DRA Brand Color Palette (python-pptx)

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

C = {
    "navy":      RGBColor(0x0F, 0x1A, 0x33),  # primary bg
    "navyMid":   RGBColor(0x1B, 0x2A, 0x4A),  # cards, blocks
    "navyLight": RGBColor(0x2C, 0x42, 0x70),  # accent blocks
    "gold":      RGBColor(0xC9, 0xA8, 0x4C),  # primary accent
    "goldBright":RGBColor(0xD4, 0xB9, 0x6A),  # bright text on dark
    "goldPale":  RGBColor(0xE8, 0xD5, 0xA3),  # muted gold
    "goldLight": RGBColor(0xF5, 0xED, 0xD6),  # tinted bg
    "white":     RGBColor(0xFF, 0xFF, 0xFF),
    "cream":     RGBColor(0xF8, 0xF6, 0xF0),  # card bg
    "creamDark": RGBColor(0xED, 0xE8, 0xDC),
    "text":      RGBColor(0x1A, 0x1A, 0x2E),  # body text
    "textMid":   RGBColor(0x4A, 0x4A, 0x5A),  # secondary text
    "textLight": RGBColor(0x7A, 0x7A, 0x8A),  # captions
    "teal":      RGBColor(0x1A, 0x7A, 0x7A),  # info cards
}
```

### Step 4 — Key Helper Functions

```python
def add_shape(slide, left, top, width, height, fill_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape

def add_rounded_rect(slide, left, top, width, height, fill_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape

def add_text_box(slide, left, top, width, height, text, font_size=14,
                 color=C["text"], bold=False, alignment=PP_ALIGN.LEFT,
                 font_name="Calibri", anchor=MSO_ANCHOR.TOP):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    try:
        tf.vertical_anchor = anchor
    except:
        pass
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox

def add_footer(slide, page_num, total):
    """DRA-branded footer bar — navy rectangle, gold text."""
    add_shape(slide, 0, SH - Inches(0.45), SW, Inches(0.45), fill_color=C["navy"])
    add_text_box(slide, Inches(0.5), SH - Inches(0.45), Inches(4), Inches(0.45),
                 "DRA Group | Project Name — Project Specifications",
                 font_size=8, color=C["gold"], anchor=MSO_ANCHOR.MIDDLE)
    add_text_box(slide, SW - Inches(1.2), SH - Inches(0.45), Inches(1), Inches(0.45),
                 f"{page_num} / {total}", font_size=8, color=C["gold"],
                 alignment=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

def add_title_bar(slide, title, subtitle=None):
    """Gold line across top + navy title with gold accent bar."""
    add_shape(slide, 0, 0, SW, Inches(0.05), fill_color=C["gold"])
    add_shape(slide, Inches(0.5), Inches(0.25), Inches(0.08), Inches(0.5), fill_color=C["gold"])
    add_text_box(slide, Inches(0.75), Inches(0.2), Inches(8), Inches(0.55),
                 title, font_size=22, color=C["navy"], bold=True)
    if subtitle:
        add_text_box(slide, Inches(0.75), Inches(0.65), Inches(10), Inches(0.35),
                     subtitle, font_size=11, color=C["textLight"])
```

### Step 5 — Upload to Drive & Convert to Google Slides

```python
from googleapiclient.http import MediaFileUpload
from tools.gws_auth import build_service

drive = build_service("drive", "v3", service_name="google-draas")

# Delete old version
for f in drive.files().list(
    q="name='Presentation Name' and trashed=false",
    fields='files(id)'
).execute().get('files', []):
    drive.files().delete(fileId=f['id']).execute()

# Upload PPTX — request Drive to auto-convert to Google Slides
media = MediaFileUpload(
    "/tmp/presentation.pptx",
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True
)
body = {
    'name': 'Presentation Name',
    'mimeType': 'application/vnd.google-apps.presentation',
}
f = drive.files().create(body=body, media_body=media, fields='id, name, mimeType, webViewLink').execute()

# Share with user
drive.permissions().create(
    fileId=f['id'],
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'psingh@draas.com'},
    sendNotificationEmail=False
).execute()

# Optional: public access
drive.permissions().create(
    fileId=f['id'],
    body={'type': 'anyone', 'role': 'reader'}
).execute()
```

### Step 6 — Deliver Link

Always deliver the Google Slides link in a code block (backticks) — Prakash reports Telegram URL rendering breaks Google Slides redirects. Also tell him to search Drive by filename as fallback.

## Design Patterns

### Cover Slide
- Full navy background (`0F1A33`)
- Gold L-shape accent in top-left corner (vertical bar 0.15" × 3.5", horizontal bar 4" × 0.15")
- "PROJECT SPECIFICATIONS" badge in gold rounded rect
- Project name in 48pt bold white
- Location + tagline in goldBright
- NavyMid bottom band (20% height) with CONFIDENTIAL notice + date

### Metric Cards Row (Slide 2)
- NavyMid rounded rect cards with gold top accent line (0.04" high)
- Large goldBright number (16pt), white label below (9pt), centered
- 6 cards in a row, ~1.9" wide each

### Room Breakdown (Slides 4-6)
- 4-column grid of cream cards
- Each card: gold left accent bar (0.04"), room name bold left, area sqft right-aligned in navyLight
- Total carpet area bar at bottom: navyMid bg, goldBright text, gold accent top line

### Villa Variants Table (Slide 3)
- Navy header row, alternating cream/white data rows
- Variant name in gold, rest in text color
- Center-aligned throughout

### Details Tables (various slides)
- Alternating cream/white rounded rect rows
- Gold left accent bar (0.06")
- Left column: textMid bold label, right column: text value

### Key Stats Footer Cards (e.g., Electrical points)
- NavyMid rounded rect, gold top accent
- Large goldBright number (24-28pt), white label below
- 4 in a row, 2.7" each

## Pitfalls

- **`docs_create` expects `body=` not `content=`**: The bridge creates a `SimpleNamespace` from kwargs. `docs_create` reads `args.body` (for the doc body text), not `args.content`. Passing `content=` raises `AttributeError`.
- **`drive_upload` requires ALL params including `parent=None`**: Missing optional params cause `AttributeError: 'SimpleNamespace' object has no attribute 'X'`.
- **python-pptx is in Hermes venv**: Use `/opt/hermes/.venv/bin/python3` or `cd /opt/hermes && .venv/bin/python3 script.py`.
- **Slides API is disabled for the GCP project**: Cannot use `presentations().batchUpdate()` to edit slides after creation. All slide content must be in the PPTX before upload. After upload, edit via PPTX → re-upload → delete old → share new.
- **Telegram link rendering**: Put Google Slides URLs in backticks so user can copy-paste into browser. Also mention Drive search-by-filename as fallback.
- **python-pptx has no native table column auto-fit**: `colW` array values must sum to the table's `w`. pptxgenjs has the same requirement.
- **python-pptx row heights**: Provide separate `rowH` array with header height as first element. Unspecified rows get default tiny height and text clips.

## Reference

Based on the Ranka Oasis session (July 2026): Google Sheet ID `16wKGxe5tIporWlLJTVwibgzm6IgnFINIj35GX8nqWOI` with 9 tabs of competitive data, villa dimensions, and specifications across premium and investor grade levels.
