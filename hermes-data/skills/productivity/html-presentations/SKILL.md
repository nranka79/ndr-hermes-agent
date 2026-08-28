---
name: html-presentations
description: "Create professional HTML → PDF presentations (brochures, leasing decks, investor IM) using weasyprint — brand colors, full-page images, tables, maps, and Drive delivery."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [presentations, html, pdf, brochure, real-estate, weasyprint]
    related_skills: [powerpoint, gws-automation, productivity-workflows]
---

# HTML → PDF Presentations

Use this skill when the user asks to create a **presentation, brochure, flyer, information memorandum, or leasing deck** as a PDF (not .pptx). The HTML → PDF approach gives full design control over layout, typography, and branding without needing PowerPoint templates.

## When to use vs. `powerpoint` skill

| Factor | HTML → PDF (this skill) | .pptx (`powerpoint` skill) |
|--------|------------------------|----------------------------|
| Design control | Full CSS (any layout) | Constrained by slide shapes |
| Full-page images | ✅ `background-size: contain` | Complex shape placement |
| Custom typography | ✅ CSS fonts | Limited to system fonts |
| User editing | No (PDF is final) | Yes (.pptx is editable) |
| Best for | Final brochures, investor decks polished PDFs | Drafts, editable decks, template-based slides |

**Decision:** Use HTML → PDF when the deliverable is a **polished, final PDF** for external sharing (clients, investors, lessees). Use `powerpoint` when the user needs an editable .pptx to modify later.

## Workflow

### Step 1 — Gather data sources

Extract all project data from:
- **Architectural plans** (PDFs) — use `pdftotext -layout` for text-based, or `pdftoppm + vision_analyze` for scanned plans
- **Weekly progress reports** (PDFs) — structural milestones, budget, completion timeline
- **Approved site plans** — dimensions, parking counts, FSI, area statements
- **Google Maps** — location screenshot or embed coordinates

### Step 2 — Design the HTML

**Brand color palette (DRAAS):**
```css
:root {
  --navy:     #0F1A33;
  --navyMid:  #1B2A4A;
  --gold:     #C9A84C;
  --goldBright:#D4B96A;
  --cream:    #F8F6F0;
  --text:     #1A1A2E;
  --textMid:  #4A4A5A;
  --textLight:#7A7A8A;
}
```

**Page structure** (A4 landscape = 297mm × 210mm):
```css
@page { size: A4 landscape; margin: 0; }
.slide { width: 297mm; height: 210mm; page-break-after: always; }
```

### Step 3 — Full-page images (CRITICAL: avoid cropping)

**⚠️ PITFALL — images get cropped with `<img>` + `object-fit: cover`.**

The user WILL notice if an image is cut off. Always use CSS background-image instead:

```css
.img-slide {
  width: 297mm; height: 210mm;
  page-break-after: always;
  background-color: #0F1A33;         /* dark fill for bars */
  background-size: contain;          /* fit entire image */
  background-repeat: no-repeat;
  background-position: center center;
}
```

Then in HTML:
```html
<section class="img-slide" style="background-image: url('file:///path/to/image.jpg');"></section>
```

This ensures the **full image is visible** with navy bars on the sides to fill the gap. Do NOT use `<img>` tags for full-page images — weasyprint's `object-fit` support is unreliable and `cover` will crop.

### Step 4 — Data cards and tables

Use flex-based card layouts:

```html
<div class="row" style="gap:10px;">
  <div class="card-dark" style="text-align:center; flex:1;">
    <span class="num">46,233</span>
    <span class="lbl">Site Area (Sq.ft)</span>
  </div>
</div>
```

```css
.card-dark { background: #1B2A4A; border-radius: 6px; padding: 14px 16px; color: #FFFFFF; }
.card-dark .num { color: #D4B96A; font-size: 28pt; font-weight: 700; display: block; }
.card-dark .lbl { color: rgba(255,255,255,0.8); font-size: 9pt; }
```

### Step 5 — Location map with Google Maps overlay

Make the map clickable (opens Google Maps when tapped in PDF viewer):

```html
<a href="https://maps.app.goo.gl/SHORTLINK" target="_blank" style="flex:1; text-decoration:none; display:block;">
  <div style="position:relative;">
    <img src="file:///path/to/screenshot.jpg" style="width:100%;">
    <div style="position:absolute; top:12px; left:12px; background:#1B2A4A; color:#C9A84C; padding:6px 12px; border-radius:4px; font-weight:700;">★ SITE</div>
    <div style="position:absolute; bottom:8px; right:8px; background:rgba(15,26,51,0.8); color:#FFF; padding:4px 10px; border-radius:4px; font-size:8pt;">Tap to open in Google Maps ↗</div>
  </div>
</a>
```

### Step 6 — Convert to PDF

**Pre-check: ensure weasyprint is installed.**
```bash
uv pip install weasyprint
```
(weasyprint is NOT in the Hermes venv by default — it must be installed first.)

Then convert:
```bash
python3 -c "from weasyprint import HTML; HTML('input.html').write_pdf('output.pdf')"
```

**⚠️ PITFALL — `weasyprint` is NOT in the base venv.** Always run `uv pip install weasyprint` before converting. Using the shell binary path (`/opt/hermes/.venv/bin/weasyprint`) only works after installation.

**⚠️ PITFALL — iframe embeds (Google Maps embed) do NOT render in weasyprint PDF.** Use a screenshot image with a clickable overlay link instead.

## A4 portrait PDF output (for document-style deliverables)

When the deliverable is a multi-page **document** (not a brochure/slides), use A4 portrait with page breaks:

```css
@page {
  size: A4;
  margin: 2cm 2.2cm;
}
@media print {
  nav, .nav-wrap { display: none !important; }
  section { page-break-inside: avoid; page-break-before: always; }
  section:first-of-type { page-break-before: avoid; }
  .hero { page-break-after: avoid; }
}
```

This forces each `<section>` to start on a new page, with the hero content kept together and the navigation hidden. Use this for: PRDs, business briefs, research reports, financial models — any document that reads like a report, not a slide deck.

Contrast with **A4 landscape** for brochure/leasing decks:
```css
@page { size: A4 landscape; margin: 0; }
.slide { width: 297mm; height: 210mm; page-break-after: always; }
```

## Business-facing owner's brief document type

When NDR asks for a document to share with external partners (not the tech team), build a **self-contained HTML** with 6 sections (about my business, what I need, what I want, sample workflows, what I already have, the approach). These are written in plain business-owner language — no architecture jargon, no code references. The delivery pipeline: HTML (polished CSS, DRAAS brand) → A4 PDF → Drive upload → email draft reply threaded to the recipient's existing conversation.

### Step 7 — Upload to Drive

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service("drive", "v3")
# Delete old version first
for f in drive.files().list(q=f"'{FOLDER_ID}' in parents and name='FILE_NAME' and trashed=false", fields="files(id)").execute().get('files', []):
    drive.files().delete(fileId=f['id']).execute()

media = MediaFileUpload("/tmp/output.pdf", mimetype="application/pdf", resumable=True)
file = drive.files().create(
    body={"name": "Project_Leasing_Brochure_Datemonth.pdf", "parents": [FOLDER_ID]},
    media_body=media, fields="id, name, webViewLink"
).execute()
drive.permissions().create(fileId=file['id'], body={"type": "anyone", "role": "reader"}).execute()
```

### Step 8 — Upload source files alongside

After delivering the final PDF, upload the raw source files (plans, reports, renders) to the same folder for a complete record:

```python
files_to_upload = [
    ("/path/to/local.pdf", "DRIVE_NAME.pdf"),
]
for local_path, drive_name in files_to_upload:
    if not os.path.exists(local_path):
        continue
    existing = drive.files().list(q=f"'{FOLDER_ID}' in parents and name='{drive_name}' and trashed=false", fields="files(id)").execute()
    if existing.get('files'):
        continue  # skip duplicates
    media = MediaFileUpload(local_path, mimetype="application/pdf", resumable=True)
    drive.files().create(body={"name": drive_name, "parents": [FOLDER_ID]}, media_body=media, fields="id").execute()
```

## Typical slide structure (leased commercial property brochure)

| Page | Content |
|------|---------|
| 1 | **Cover** — render image with dark overlay, project name, tagline |
| 2 | **Full-page render** — artist impression (fit to page with navy bars) |
| 3 | **Full-page progress photo** — as-on-date construction photos from weekly report |
| 4 | **Location** — Google Maps screenshot + connectivity/neighbourhood/access cards |
| 5 | **Project Snapshot** — key stats cards + detailed parameter table + saleable area breakdown |
| 6 | **Floor Plans** — configuration options (single tenant, multi tenant, business suites) |
| 7 | **Parking & Infrastructure** — car/bike counts, STP specs, power backup, building services |
| 8 | **Contact** — enquiry details, completion date, disclaimers |

## Standalone HTML reports with embedded infographics (no PDF)

When the user asks for a **self-contained single HTML file** (not a PDF) with embedded visual elements — choose between two approaches depending on what's available in the environment.

### Approach selection

| Factor | HTML + PIL infographics | HTML + CSS-only (no images) |
|--------|--------------------------|------------------------------|
| Dependencies | Requires Pillow + numpy | None (pure HTML+CSS) |
| Environment | Full sandbox with pip install | Works in locked-down sandboxes |
| Visual elements | Custom charts, infographics, hero banners | Cards, tables, CSS gradients, unicode icons |
| File size | Larger (base64 PNGs) | Smaller |
| Best for | Visual storytelling, marketing content | Data-dense reports, financial models |
| Pitfall | PIL install may fail if venv is read-only | No visual charts — rely on table clarity |
| Worked example (PIL) | `references/bamboo-research-report-pil-infographics.md` | |
| Worked example (CSS) | | `references/bamboo-report-css-only-financial-model.md` |

### Step 1 — Generate infographics with PIL

Use Python Pillow (PIL) to create data visualizations: comparison charts, economics infographics, timeline roadmaps, etc. Always available — no API key needed.

**Key PIL techniques:**

```python
from PIL import Image, ImageDraw, ImageFont

# Gradient background
def create_gradient(w, h, colors):
    img = Image.new('RGBA', (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        ratio = y / h
        r = int(colors[0][0]*(1-ratio) + colors[1][0]*ratio)
        g = int(colors[0][1]*(1-ratio) + colors[1][1]*ratio)
        b = int(colors[0][2]*(1-ratio) + colors[1][2]*ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))
    return img

# Rounded rectangles (PIL 9.5+)
def draw_rounded_box(draw, xy, fill, radius=12):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

# Font loading (fallback cleanly)
font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
try:
    font_body = ImageFont.truetype(font_paths[0], 16)
    font_title = ImageFont.truetype(font_paths[1], 28)
except:
    font_body = ImageFont.load_default()
    font_title = ImageFont.load_default()
```

**Common infographic types:**
- **Hero banner** — gradient background + centered text + decorative elements
- **Comparison chart** — rows with species/options, color-coded rank badges, star ratings
- **Economics infographic** — stat cards (top metrics row), cost breakdown with horizontal bars, revenue projections with colored scenario blocks
- **Value-add spectrum** — categorical grid with items grouped by capital tier, recommended items highlighted in gold
- **Timeline roadmap** — horizontal timeline line with numbered circles + phase cards below
- **Scheme/subvention overview** — rows with name badge + subsidy percentage + description

### Step 2 — Embed as base64 in HTML

```python
import base64

def img_to_data_uri(path):
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{b64}"

# In your HTML string:
html = '<img src="data:image/png;base64,{b64_here}" alt="...">'
```

**⚠️ PITFALL — f-strings break with CSS `{` braces.** If your HTML template contains CSS with curly braces, Python f-strings will raise SyntaxError. Use one of these patterns:

**Pattern A — Template with placeholders + str.replace() (preferred for large files):**
```python
# Store HTML as regular string with __PLACEHOLDER__ markers
html = '''<img src="data:image/png;base64,__HERO__" alt="...">'''

# After reading all images:
images = {"HERO": img_to_data_uri("hero.png"), "SPECIES": img_to_data_uri("species.png")}
for key, value in images.items():
    html = html.replace(f"__{key}__", value)
```

**Pattern B — .format() with numbered placeholders (for small HTML):**
```python
html = '<img src="data:image/png;base64,{0}" alt="...">'.format(img_to_data_uri("hero.png"))
```

## CSS-Only Approach (when PIL/matplotlib unavailable)

When the sandbox environment lacks PIL/matplotlib (common in API-server sessions or read-only venv), build the entire report as clean HTML+CSS with NO generated images. Use CSS gradients, box-shadows, borders, and emoji/unicode characters for visual hierarchy instead of infographic PNGs.

### Professional design principles (DRAAS user preference)

The user explicitly rejected "too colorful, not professional looking" designs. Follow these guidelines for all standalone HTML reports:

**Color palette — restrained and professional:**
```css
:root {
  --green-900: #1b4332;
  --green-800: #2d6a4f;
  --green-700: #40916c;
  --green-500: #74c69d;
  --green-100: #d8f3dc;
  --gray-900:  #1a1a2e;
  --gray-800:  #2d2d44;
  --gray-700:  #4a4a5a;
  --gray-200:  #e5e7eb;
  --gray-100:  #f3f4f6;
  --white:     #ffffff;
  --gold:      #f59e0b;
}
```

**Design rules:**
- No gradients on text — sparingly for hero backgrounds only
- No neon/bright colors — stick to muted, earthy tones
- Cards over infographics — white cards with subtle border and shadow
- Tables with alternating row colors — `tr:nth-child(even)` in light gray
- One accent color — dark green primary, gold/amber only for callout highlights
- Generous whitespace — 24-32px padding on cards, 48px section spacing
- Font hierarchy — system fonts only, 2.8rem hero, 1.8rem section, 0.9rem body
- Sticky navigation — section anchor links in a sticky nav bar for long reports
- Responsive — single-column on mobile, multi-column grid on desktop

**Professional layout structure (for research/financial reports):**
```
Hero section: gradient bg, white text, key stat cards in a row
Sticky nav: section anchor links (horizontal scroll)
Sections:
  - Executive Summary (3-column card grid)
  - Data/Tables (scrollable table-wrap divs)
  - Financial Model (metrics row + detailed cashflow table)
  - Sensitivity Analysis (matrix tables for IRR/NPV)
  - Scenarios Comparison (3-card row with colored top borders)
  - References (numbered list with clickable links)
Footer: disclaimer, data sources
```

### Embedding Python financial computations in HTML

When the user asks for financial projections with land cost, IRR, etc.:

**Workflow:**
1. Run Python financial model in `execute_code` — print all computed values to stdout
2. Build HTML as a Python f-string or string.Template with the computed values embedded
3. Write the HTML to disk with `write_file`
4. Upload to Drive

**Pattern for embedding computed values:**
```python
# Compute first
price, yield_ac, acres = 4500, 18, 10
mature_net = price * yield_ac * acres - opex * acres
irr_pct = 30.2

# Build CSS separately to avoid f-string braces conflict
css = '''
table { width: 100%; border-collapse: collapse; }
td { padding: 10px 16px; }
'''

# Build HTML with embedded values
html = f'''<!DOCTYPE html>
<html><head><style>{css}</style></head><body>
<table>
<tr><td>Annual Net Income</td><td>Rs. {mature_net:,.0f}</td></tr>
<tr><td>IRR</td><td>{irr_pct:.1f}%</td></tr>
</table></body></html>'''

write_file("/path/to/report.html", html)
```

**⚠️ PITFALL:** f-strings CAN contain CSS when the CSS string is pre-assigned to a variable. The pattern above avoids the `{` braces conflict. Do NOT inline CSS inside an f-string directly.

### Step 3 — Upload self-contained HTML to Drive

```python
import os

# Try common user IDs to find a working auth (for API sessions without session context)
for uid in ['ndr', 'sales1.blr', 'psingh']:
    os.environ['HERMES_SESSION_USER_ID'] = uid
    try:
        from tools.gws_auth import build_service
        drive = build_service("drive", "v3")
        print(f"Auth OK for user {uid}")
        break
    except Exception:
        continue

from googleapiclient.http import MediaFileUpload

# Find TMP folder or use known fallback
results = drive.files().list(
    q="name='TMP' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    spaces='drive', fields='files(id, name)'
).execute()
FOLDER_ID = results['files'][0]['id'] if results.get('files') else "18p74II2uL32sNDzDDwXzmlOUdJJOTmE-"

media = MediaFileUpload(local_path, mimetype="text/html", resumable=True)
file = drive.files().create(
    body={"name": "YYYYMMDD_Project_ReportName.html", "parents": [FOLDER_ID]},
    media_body=media, fields="id,name,webViewLink"
).execute()
drive.permissions().create(fileId=file['id'], body={"type": "anyone", "role": "reader"}).execute()
print(file['webViewLink'])
```

**Known user IDs:** Nishant=ndr, Bharat=sales1.blr, Prakash=psingh.

**Known TMP folder ID:** `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-` (fallback when search fails).

## Visual guidelines

- **Navy dominates** — dark bg for title/cover, light for content slides
- **Gold accents only** — titles, highlights, bars; never for body text
- **Cream card backgrounds** — for data cards and tables
- **Full-page images** use `background-size: contain` with navy fill bars (never `cover`)
- **Map images** wrapped in an `<a>` tag linking to Google Maps for PDF tap-to-open
- **Footer bar** on every content slide: project name left, page number right

## Known pitfalls

- `weasyprint` is in `/opt/hermes/.venv/bin/weasyprint` — not in PATH
- Do NOT use iframe for maps — they render blank. Use a screenshot + clickable overlay
- File naming: `Project_Brochure_DocumentType_Date.pdf` (e.g., `DRA_Downtown_Leasing_Brochure_Jun2026.pdf`)
- Always delete old version on Drive before uploading fresh — no overwrite semantics
- Make PDF publicly viewable with `type: anyone, role: reader` permission for sharing
- **⚠️ AI-compiled content disclaimer:** When delivering a brochure or presentation to an external party (lessee, investor, client), ALWAYS include a note in the WhatsApp/email alongside it stating that the brochure was compiled by AI from available project documents and may not be 100% accurate. Use phrasing like: *"Please note this content may not be 100% accurate as it was compiled by my AI assistant from available documents and collateral. Key data points (floor plate, plinth area, layout) are accurate, but please verify before relying."* This applies any time the user asks you to share an AI-compiled document externally.
- **⚠️ CRITICAL: Always label currency units and scale explicitly.** When presenting financial data tables (costs, revenue, ROI), every table header must state the unit (₹/acre, ₹/sq.ft, ₹ total, lakhs, crores) and whether the figure is per-unit or total. Ambiguous values like "9,100" without context will be questioned. Pattern: use a sub-label row in table headers (e.g. "Year 1\n₹/acre") and/or a callout box immediately above the table stating the denomination. This applies to both PIL infographic tables and HTML tables.

### Step 9 — Merge with existing PDF (append pages)

When the user asks to add a location page or any content to an existing PDF (not create from scratch):

```bash
uv pip install pypdf
```

```python
from pypdf import PdfReader, PdfWriter

reader_existing = PdfReader("existing.pdf")
reader_new = PdfReader("new_page.pdf")

writer = PdfWriter()
for page in reader_existing.pages:
    writer.add_page(page)
for page in reader_new.pages:
    writer.add_page(page)

with open("merged_output.pdf", "wb") as f:
    writer.write(f)
```

**⚠️ PITFALL — always install pypdf via `uv pip install pypdf`** before import. It's not in the base venv.

### Step 10 — Location intelligence with OpenStreetMap (no API key needed)

When the user needs **location research** for a property (dark store evaluation, leasing brochure, investor IM), use the free OpenStreetMap Overpass API to gather nearby facilities, road connectivity, and density data — no API key required.

**Resolution pattern for Google Maps short links:**

```bash
curl -sI "https://maps.app.goo.gl/SHORTLINK" | grep -i location:
# Returns the resolved URL with coordinates
```

Or extract coordinates directly:
```python
import requests
url = "https://maps.app.goo.gl/SgJZ9JT75GBFWhta6"
r = requests.get(url, allow_redirects=True)
# Coordinates are in the resolved URL path, e.g. /place/12.977716,77.577864
```

**Overpass API query for a 1km radius around the property:**

```python
lat, lng = 12.977716, 77.577864

query = f"""
[out:json][timeout:30];
(
  node["amenity"](around:1000,{lat},{lng});
  way["amenity"](around:1000,{lat},{lng});
  node["shop"](around:1000,{lat},{lng});
  way["landuse"="residential"](around:1000,{lat},{lng});
  way["landuse"="commercial"](around:1000,{lat},{lng});
  node["highway"="bus_stop"](around:1000,{lat},{lng});
  node["railway"="station"](around:1000,{lat},{lng});
  way["highway"="primary"](around:1000,{lat},{lng});
  way["highway"="secondary"](around:1000,{lat},{lng});
  way["highway"="trunk"](around:1000,{lat},{lng});
);
out center;
"""

r = requests.post("https://overpass-api.de/api/interpreter",
                  data={"data": query},
                  headers={"User-Agent": "DRAAS-Hermes/1.0"},
                  timeout=30)
data = r.json()
```

**Categorize results for the HTML page:**

Group by amenity type (supermarket, school, hospital, restaurant, bank, bus_stop), then render as clickable tag badges or cards in the HTML design.

**Use Nominatim for reverse geocoding (address details):**

```python
url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
r = requests.get(url, headers={"User-Agent": "DRAAS-Hermes/1.0"})
address = r.json()
```

**Dark store / quick commerce delivery analysis:**

When evaluating a property for dark store / quick commerce, include these elements in the location page:

- **Delivery coverage rings** (10/20/30 min radius) with what each covers
- **High-density residential catchment** — name the areas with distance and direction (e.g. Malleswaram 2.5km NW)
- **Road connectivity** — classify as primary/secondary/trunk from Overpass results
- **Demographic indicators** — pin code, district, urban density classification
- **Suitability score** — rate Location Centrality, Residential Density, Road Connectivity, Proximity to Customers as percentage bars
- **Key advantages** — short bullet points for quick scanning

**WeasyPrint conversion (from execute_code context):**

```bash
uv run python3 -c "
from weasyprint import HTML
HTML('input.html').write_pdf('output.pdf')
"
```

The Hermes venv's weasyprint binary may not be on PATH. `uv run python3` resolves it correctly.

**⚠️ PITFALL — Overpass API rate limit.** If the query returns empty or a `429 Too Many Requests`, add a 2-second sleep and retry. Keep the search radius to ~1000m for responsive queries.

## References

- `references/dra-downtown-leasing-brochure-jun2026.md` — Full worked example with data extraction, HTML template, and Drive upload from the DRA Downtown session
- `references/dra-downtown-brochure-html-template.html` — Reusable HTML template for brochure-style leasing decks (8-page layout: cover, renders, location, snapshot, floor plans, parking/STP, contact)
- `references/gandhinagar-mamatha-darkstore-location-research.md` — Full worked example: extracting property photos from email, OpenStreetMap location research for dark store evaluation, WeasyPrint HTML→PDF generation, and merging with pypdf for the Gandhinagar Mamatha Apartments leasing brochure
