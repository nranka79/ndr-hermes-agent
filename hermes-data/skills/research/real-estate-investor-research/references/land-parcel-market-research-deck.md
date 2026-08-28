# Land Parcel Market Research Deck (Nandi Hills / Chikkaballapur format)

Trigger: user shares a land sketch PDF + Google My Maps link + competitor spreadsheet
(or says "similar to the Nandi Hills presentation, prepare for <location>") and wants a
branded DRA market research deck for a land parcel (plotted / villa-plots investment case).

Worked example: `Chikkaballapur(Arasanahalli Lands) - 40 Acres` deck (45 slides),
built 2026-08-03 from `arasanahalli-kuppahalli-sketch.pdf`, My Maps
`mid=1uzS8A-farIA8ogNCEEFxb3DixUf1hCk`, and a stacked competitor sheet.

## Pipeline overview
1. **Ingest**: render sketch PDF to PNG (`pdftoppm -png -r 200`), pull My Maps KML, parse the competitor sheet.
2. **Compute**: boundary polygon area + centroid, haversine distances subject → every competitor pin.
3. **Research**: govt/registry benchmarks, land deals, infra drivers for that corridor (web_search).
4. **Build**: python-pptx deck following the Nandi Hills v4 formula (below).
5. **QA**: upload as Google Slides → export PDF → pdftoppm montage → vision_analyze.
6. **Deliver**: code-block link + Drive-filename fallback, shared writer with psingh@draas.com.

## 1. My Maps KML export & parse (no API key)
- Export endpoint: `curl -sL "https://www.google.com/maps/d/u/0/kml?mid=<MID>&forcekml=1"` (add a browser UA).
- Parse `<Placemark>` blocks with regex. Placemark names carry:
  - `Land Boundary` → polygon (21+ coords) → the subject envelope
  - every other pin → competitor project name + point (centroid)
- Polygon area via spherical shoelace:
```python
import math
def poly_area_m2(pts):
    n = len(pts); area2 = 0.0; R = 6371000.0
    for i in range(n):
        lat1, lon1 = pts[i]; lat2, lon2 = pts[(i+1) % n]
        lat1r, lon1r = math.radians(lat1), math.radians(lon1)
        lat2r, lon2r = math.radians(lat2), math.radians(lon2)
        area2 += (lon2r - lon1r) * (2 + math.sin(lat1r) + math.sin(lat2r))
    return abs(area2 * R * R / 2.0)
```
- Haversine distance from subject centroid to each pin → rank closest comparables (the true micro-market comps, e.g. VSR Rejoice at 0.6 km).

## 2. Stacked single-column Google Sheet parse
- DRA competitor trackers are often ONE column, one field per row, ~13 fields per record:
  project, developer, location, coords, rera, launch, phase, price(launch+current concatenated), area, units, amenities, source1, source2 — with blank rows between.
- **PITFALL**: record-number marker rows (2, 3, 4 …) frequently merge into the previous field's text
  (e.g. `Trails99acres Map & Details4`). Do NOT split on number rows. Instead: drop the header, chunk
  the remaining non-empty values into 13-field blocks, then verify each block starts with a known
  project name (cross-check against the My Maps pins). 14 records × 13 fields parsed cleanly this way.
- Appreciation band: `+min(current)/max(launch)` to `+max(current)/min(launch)`.

## 3. Deck formula (Nandi Hills v4 — 45 slides for 16 projects)
1. Title — navy full-bleed, gold rule at bottom, big white title + gold subtitle, survey line, CONFIDENTIAL tag
2–4. Exec summaries: Land & Development (facts left, DEVELOPMENT POTENTIAL card right) / Launch Price & Velocity (benchmarks left, VELOCITY card right) / Land Price Benchmarks (govt+registry left, market deals right, footer note)
5. Subject Land Overview — PROJECT chip; rows: Project Name / Location / Land Area / Development Type / Connectivity / Nearest Hub; survey-number block at bottom
6. Land Joint Sketch — sketch image right (fit portrait), SURVEY DETAILS panel left
7. Location USP & Connectivity — icon + bold navy title rows
8. Section divider — navy, gold band, PLOTTED PROJECTS IN THE VICINITY
9–40. Per project × 2 slides:
   - Project page: 3 KPI cards (💰 CURRENT / 🚀 LAUNCH / 📈 APPRECIATION) + QUICK FACTS + PROJECT DETAILS (location, launch, RERA, area, amenities, sources). **QUICK FACTS = Type / Status / Units / Developer ONLY** — Units already carries the size range ("345 Plots (1,200–3,000 sq.ft)"), so a separate Sizes row is redundant. User correction 2026-08-03 ("check the alignment, remove non required fields"): drop Sizes, keep the four rows.
   - Market review page: ✅ HIGHLIGHTS / ⚠️ CONCERNS / 📊 MARKET REPUTATION / 💡 WHY BUY / INVEST + source line
41. Key Infrastructure & Demand Drivers — 6 rows with HIGH/MEDIUM IMPACT navy chips
42. Price comparison table — 8 cols (Project/Type/Launch/Current/Appreciation/Location/Launch/Status), **amber subject row** at top, navy header. **PITFALL (fix applied 2026-08-03):** 18 rows with long cell text auto-expand past the slide bottom and the last row collides with the footer. Compact recipe: 8.5pt data cells (10pt header), per-project short-value maps for Location ("Chikkaballapur Belt", "Nandi Hills Rd") and Status ("Delivered", "Existing"), explicit row heights ~0.036×SH, tight cell margins (18k EMU top/bottom, 36k L/R), footer at 0.915×SH instead of 0.93.
43. Product-fit analysis — 3 option cards (A RECOMMENDED navy, B/C gold chips)
44. Pricing recommendation — strategy card + phasing/approvals/risk card
45. Thank you

Reusable constants (16:9 EMU): slide 12191675 × 6858000; NAVY #1F3864, GOLD #D4A53C,
CREAM #F7F3EA, LIGHT_GOLD #FBF2DE, AMBER #F4B400. Header helper: gold accent bar
(L=4%SW, T=5.5%SH, W=1.2%SW, H=7.5%SH) + title + navy tag chip top-right (W=14%SW).
Build with `/opt/data/.venv/bin/python` (python-pptx 1.0.2; system python has no pptx).

Before building a clone of a reference deck, dump every slide's shapes with python-pptx
(left/top/width/height + first text line) — the coordinates are directly reusable.

## 4. QA without LibreOffice
- No LibreOffice on the VPS → upload pptx as native Google Slides
  (`drive.files().create`, mimeType `application/vnd.google-apps.presentation`),
  export PDF (`files().export_media`), `pdftoppm -r 110 -f N -l N`, montage 2×2 with PIL,
  then `vision_analyze` the montage for overflow / overlap / cut-off.
- Also scan the pptx programmatically (slide count, key strings, table dims).

### Drive-API-only verification of the LIVE deck (Slides API may be disabled)
The GCP project behind the gws-vault token may not have the Slides API enabled —
`slides.googleapis.com` reads (e.g. `presentations().get()` to dump slide text) fail with
403 SERVICE_DISABLED. Do NOT switch to that path; verify the live deck entirely through Drive:
1. `drive.files().list(q="name contains '<deck>' and trashed = false")` → confirm exactly one
   non-trashed copy (old versions must be trashed before re-upload).
2. Export the live PDF:
```python
from googleapiclient.http import MediaIoBaseDownload
fh = io.BytesIO()
req = drive.files().export_media(fileId=deck_id, mimeType='application/pdf')
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
open('/tmp/deck.pdf', 'wb').write(fh.getvalue())
```
   **PITFALL: `req.execute()` on export_media returns 0 bytes silently** (empty file, no error) —
   the MediaIoBaseDownload / next_chunk loop is mandatory.
3. `pdfinfo` for page count (expect the exact slide count), `pdftoppm -f N -l N -r 110-150 -png`
   for the slides you actually need to check, `vision_analyze` each with a targeted question.
4. **Color checks need visual mode:** OCR-only output from `vision_analyze` cannot confirm the
   amber subject row — pass `also_describe_visually=true` (or ask "which row is highlighted")
   to verify the AMBER row exists at the top of the price table.

### Spot-check map (45-slide Nandi/Chikkaballapur format)
After a rebuild, render and verify at least: slide 2 (exec summary values not clipped),
slide 9 (first project page: no Sizes row, no coords, no Sources row — only QUICK FACTS
Type/Status/Units/Developer + compact portal source line), slide 42 (price table — the
last row Mantri Hills must clear the footer, source line visible below; note infra is slide
41, price table 42). Check title/divider/thank-you once per build, not every round.

## 5. Corrections / re-upload
- After a content fix: trash the old Slides file, re-upload with the **same name**
  (the user searches Drive by filename), deliver the new link. Name format:
  `Chikkaballapur(Arasanahalli Lands) - 40 Acres` (location + extent).

## Pitfalls (learned the hard way)
- **Survey-number lists with ranges expand.** "121/1–14", "124/1A–6" etc. are many individual
  parcels. COUNT them before writing "~N survey numbers": the 62 listed + Sy 5–12 block = ~70,
  not ~55. A wrong count survives QA unless you check the arithmetic.
- **KML boundary ≠ stated acreage.** The drawn Land Boundary polygon may be much larger than the
  acquisition (71 ac envelope vs 40 ac stated). Keep the user's stated extent in the deck and
  flag the discrepancy in the delivery message — do not silently use either number.
- **Compute distances before writing connectivity claims** (don't guess "4 km from Nandi Hills" —
  verify: subject 4.1 km summit, 5.4 km Chikkaballapur town, 21.3 km KIA, closest comp 0.6 km).
- **User profile (Prakash):** Google Slides links break in Telegram → deliver the URL inside a
  plain code block and tell him to search Drive by filename as fallback. Files are owned by
  psingh@draas.com and shared writer.
- **Drive upload 500s are transient.** `drive.files().create` with a pptx media body can return
  HttpError 500 ("Internal Error") — just sleep ~5s and retry the same create; it succeeds on the
  second attempt. If the old file was already trashed before the failed upload, re-create under the
  same name; do not treat the 500 as a file/account problem.
- **After a user "fix alignment / remove fields" round, re-verify by exporting the PDF again** —
  QA montages catch table-overflow and redundant rows only if you re-render after the rebuild,
  not by trusting the fixed source code.
