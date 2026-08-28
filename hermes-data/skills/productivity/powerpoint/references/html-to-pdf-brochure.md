# HTML → PDF Brochure / Leasing Presentation

When the user asks for a **"presentable PDF"** (brochure, leasing deck, project summary) rather than an editable PPTX, use HTML + WeasyPrint instead of pptxgenjs. This gives full CSS layout control with no npm dependency.

## When to use

- User says "create a PDF" or "make a brochure" or "presentable PDF"
- You have structured project data (tables, KPIs, milestones) and render/plan images
- The output needs to look professional but doesn't need to be editable by the user
- You need richer typography, gradients, or image overlays than pptxgenjs supports easily

**If the user explicitly asks for .pptx** — use the standard pptxgenjs path (see pptxgenjs.md). This is an *alternative* for PDF-only requests.

## Available tool

```bash
# WeasyPrint is installed in the Hermes venv — NOT on PATH
/opt/hermes/.venv/bin/weasyprint input.html output.pdf
```

## Brochure structure (DRA Downtown leasing brochure — verified Jun 2026)

This is the approved structure for a DRAAS leasing brochure. **Do NOT include a construction progress page** — leasing prospects need the finished product vision, not build status.

| Page | Content | Layout |
|------|---------|--------|
| 1 | **Cover** | Full-bleed render image + dark gradient overlay, project title, "Office Space for Lease" label, address, footer |
| 2 | **Full-Page Render** | Artist impression / finished-look render, full-bleed, no text overlay |
| 3 | **Full-Page "As On Date" Photo** | Current-day site photo, full-bleed, no text overlay |
| 4 | **Location** | Left: embedded map screenshot (clickable — opens Google Maps). Right: 3 info cards (Connectivity, Neighbourhood, Access) |
| 5 | **Project Snapshot** | Top: 4 metric cards (site area, BUA, floors, height). Two-column: left = parameter table, right = saleable area breakdown |
| 6 | **Floor Plans** | 2×2 grid of plan configuration cards with specs |
| 7 | **Parking & Infrastructure** | Left: parking cards (cars + bikes + electrical). Right: STP card + building services (incl. 100% power backup) |
| 8 | **Contact** | Centered CTA, key stats summary, contact bar, disclaimer |

### Leasing brochure vs Investor deck — what to exclude

| Item | Leasing Brochure | Investor Deck |
|------|-----------------|---------------|
| Construction progress | ❌ Remove entirely | ✅ Include milestones, budget, schedule |
| Cost / budget breakdown | ❌ Remove | ✅ Include |
| Financial returns / IRR | ❌ Remove | ✅ Include |
| Render impressions | ✅ Page 2 | ✅ Cover |
| As-on-date photos | ✅ Page 3 | Optional |
| Parking + STP details | ✅ Essential for tenants | ✅ Good to have |
| Floor plan configurations | ✅ Essential for tenants | ✅ Include |
| Power backup | ✅ Essential for tenants | Optional |

## Cover image pattern

Use a render/visual image as full background with dark gradient overlay for text readability:

```css
background: linear-gradient(rgba(15,26,51,0.65), rgba(27,42,74,0.75)),
            url('file:///path/to/render.jpg') center/cover no-repeat;
```

WeasyPrint supports `file://` URLs for local files. The PDF will embed the image.

## Full-page image slides

For pages 2 and 3 (render + current photo), use a dedicated slide class with no text layout:

```html
<style>
.img-slide { width: 297mm; height: 210mm; page-break-after: always; overflow: hidden; }
.img-slide img { width: 100%; height: 100%; object-fit: cover; display: block; }
</style>

<section class="img-slide">
  <img src="file:///path/to/image.jpg" alt="DRA Downtown — Artist Impression">
</section>
```

## Brand palette (DRAAS — verified)

```css
--navy:      #0F1A33;   /* primary backgrounds */
--navy-mid:  #1B2A4A;   /* cards, secondary blocks */
--gold:      #C9A84C;   /* accents, highlights */
--gold-bright:#D4B96A;  /* text on dark bg */
--cream:     #F8F6F0;   /* card backgrounds */
--text:      #1A1A2E;   /* body */
--text-mid:  #4A4A5A;   /* secondary text */
--text-light:#7A7A8A;   /* captions */
--teal:      #1A7A7A;   /* secondary accent */
```

Apply: navy for dark backgrounds (title/conclusion), cream for content cards. Gold for emphasis accents only.

## Key CSS patterns

### A4 Landscape page
```css
@page { size: A4 landscape; margin: 0; }
.slide { width: 297mm; height: 210mm; page-break-after: always; }
.slide-inner { padding: 20mm 22mm 22mm 22mm; }
```

### Data cards
```css
.card-dark { background: #1B2A4A; border-radius: 6px; padding: 14px 16px; color: #FFFFFF; }
.card-dark .num { color: #D4B96A; font-size: 28pt; font-weight: 700; }
.card-dark .lbl { color: rgba(255,255,255,0.8); font-size: 9pt; }
```

### Tables
```css
th { background: #1B2A4A; color: #FFFFFF; padding: 8px 10px; }
td { padding: 7px 10px; border-bottom: 1px solid #E5E7EB; }
tr:nth-child(even) td { background: #F8F6F0; }
```

### Parking cards
```css
.parking-card { flex: 1; background: #F8F6F0; border-radius: 8px; padding: 16px;
  text-align: center; border: 2px solid #E5E7EB; }
.parking-card .count { font-size: 32pt; font-weight: 700; color: #0F1A33; }
.parking-card .req { font-size: 8pt; color: #7A7A8A; }
```

### Progress/Milestone grid
```css
.milestone-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.milestone-item { background: #F8F6F0; border-radius: 4px; padding: 8px 10px; text-align: center; }
```

## Source data extraction (pre-brochure)

Before creating the HTML, extract all data from project documents:

1. **Weekly Progress Report** (text-based PDF) → `pdftotext -layout` → extract: site area, BUA, budget, milestones, schedule, quality stats
2. **Approved Site Plan** (scanned PDF) → `pdftoppm -jpeg -r 200` + `vision_analyze` → extract dimensions, FSI, parking counts
3. **Architectural Plans** (text-based or scanned) → parking achieved/required, floor areas, configurations
4. **Render images** → use as cover background (pick largest/most colorful)

### Key parking data fields to extract
From the approved plan / stilt floor plan:
- Car parking required vs achieved (e.g., 67 required / 71 achieved)
- Bike parking required vs achieved (e.g., 271 required / 304 achieved)
- Format: `🚗 71` with `Required: 67 | Achieved: 71`

### Key area data fields
From the sanctioned plan / weekly report:
- Site area (e.g., 46,233 sqft)
- Total BUA (e.g., 1,09,353 sqft)
- Saleable area
- Total FSI area and achieved FSI
- Floor-wise breakdown (stilt, typical floor plinth, carpet)
- Business suite office unit sizes (carpet/plinth/saleable per unit)

## Clickable Map Links (verified Jun 2026)

The user wanted the map screenshot on the Location page to open Google Maps when tapped in the PDF viewer. WeasyPrint preserves `<a>` tags as clickable links in the output PDF.

**Pattern:**

```html
<div style="display:flex; flex-direction:column; height:100%;">
  <a href="https://maps.app.goo.gl/XXXXXX" target="_blank" 
     style="flex:1; text-decoration:none; display:block;">
    <div style="height:100%; ... position:relative;">
      <img src="file:///path/to/screenshot.jpg" 
           style="width:100%; height:100%; object-fit:cover;">
      <div style="position:absolute; top:12px; left:12px; background:#1B2A4A; 
                  color:#C9A84C; padding:6px 12px; border-radius:4px; 
                  font-size:10pt; font-weight:700;">★ SITE</div>
      <div style="position:absolute; bottom:8px; right:8px; 
                  background:rgba(15,26,51,0.8); color:#FFFFFF; 
                  padding:4px 10px; border-radius:4px; font-size:8pt;">
        Tap to open in Google Maps ↗</div>
    </div>
  </a>
  <div style="background:#1B2A4A; color:rgba(255,255,255,0.7); 
              padding:4px 10px; border-radius:0 0 6px 6px; 
              font-size:8pt; text-align:center;">
    📍 Address here</div>
</div>
```

**Google Maps deep link:** Use the short `maps.app.goo.gl/XXXXXX` link from the user's share or a `https://www.google.co.in/maps/place/...` URL. The user typically provides this alongside a screenshot.

## Outline-first workflow (Nishant preference — verified Jun 2026)

For DRAAS brochures/project summaries, Nishant prefers:
1. **Present an outline** of pages/sections before building the full document
2. Get confirmation (he says "folder location and sub folder names are both ok" or equivalent)
3. Build the full HTML → PDF
4. Deliver for review → iterate on feedback

Present the outline as a clean numbered list showing what goes on each page. Do NOT include images or full text in the outline — just topic + 1-line description per page.

## Using user-uploaded images from cache

When the user uploads images (render views, Google Maps screenshots, project photos) via Telegram, they land in:
- `/data/hermes/image_cache/img_*.jpg` — JPEG images
- `/data/hermes/document_cache/doc_*.pdf` — PDF files

Use these paths directly with `file://` URLs in the HTML. WeasyPrint will embed them into the PDF. The image is already on disk — no download needed.

**What to expect during a brochure session:**
1. User may upload multiple images (renders, photos, screenshots) interspersed with conversation
2. Each arrives via Telegram at a different time — check cache between turns
3. Confirm with user what each image is ("render pic to use" / "as on date actual")
4. Swap the image into the HTML, regenerate, and update Drive

## Pitfalls

- **Google Maps iframes DON'T render in WeasyPrint.** The embed will be blank. Always use a static image (provided by user or via screenshot).
- **WeasyPrint path is NOT on PATH** — always use `/opt/hermes/.venv/bin/weasyprint`
- **`file://` URLs must be absolute paths.** WeasyPrint resolves them relative to the HTML file location.
- **Cover render images can be large** (500KB+ JPEG). PDF jumps from ~80KB to 500KB+. Acceptable.
- **WeasyPrint may not render all web fonts** — stick to system fonts (Calibri, Arial, Georgia, DejaVu).
- **Page breaks:** Use `page-break-after: always` on each `.slide` / `.img-slide` element.
- **Avoid nested flex layouts deeper than 2 levels** — WeasyPrint rendering gets unpredictable.
- **Version numbering:** The user typically gets multiple iterations. Use Drive delete + re-upload (not versioning) — Drive creates new file IDs each upload. Delete old before uploading new.
- **User images not immediately available in cache:** Telegram processes images asynchronously. If the user says "attaching" but no file appears in cache after 1-2 turns, the image wasn't sent or is still processing. Ask the user to resend.
- **Vision_analyze may fail on render images** (colorful building renders, Google Maps screenshots). Don't block on this — the user already told you what the image is. Use file properties (size, dimensions, mode) as confirmation instead.

## QA (visual inspection)

After generating the PDF, render it to images for visual verification:

```bash
pdftoppm -jpeg -r 150 output.pdf preview
```

For a quick check, inspect key pages with `vision_analyze` looking for:
- Text overflow/cutoff at card boundaries
- Table alignment and column width consistency
- Cover image rendering correctly (visible under gradient overlay)
- Footer text on every slide page (not on full-page image slides 2-3)
- Full-page image slides filling the entire canvas (no blank margins)
- Map screenshot visible (not a blank space)
- Page numbers match the intended order
