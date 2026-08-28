# AutoCAD Plan / CDP Map / Stage-Table Reading — Land Proposal Intake

Verified 2026-08-01 on the Arasanahalli/Kuppahalli 40A proposal (Nandi Hobli, Chikkaballapura) and the Chikkaballapur CDP map.

## When to use
- User shares a "property sketch" / "layout plan" / "model" PDF that is AutoCAD-generated (check `pdfinfo` Creator: "AutoCAD 2022..." / Producer: "pdfplot16.hdi...")
- User shares a CDP (Comprehensive Development Plan) zoning map and asks "is this zoned residential?"
- User shares a stage-wise survey-number table (colour-coded stages with owner/extent columns)

## 1. AutoCAD plan PDF → extractable detail

**Plain `pdftotext` and single-pass `pdftoppm` + OCR FAIL on A2 AutoCAD plans.** OCR of the full page returns only the title block header (e.g. "HOBLI: NANDI / TALUK: CHICKKABALLAPURA / VILLAGE: ARASANAHALLI & KUPPAHALLI") and nothing from the drawing body. The drawing content is graphical (vector lines + small text), not text-layer.

**Working recipe (quadrant split):**
```bash
# 1. Inspect metadata first — tells you it's AutoCAD + creation date + page size
pdfinfo "sketch.pdf"        # Creator: AutoCAD 2022, Page size: 1191 x 1684 pts (A2)

# 2. Render at HIGH DPI (200-300), NOT the default 72-150
pdftoppm -png -r 300 "sketch.pdf" /tmp/sketch_300

# 3. Split into 4 quadrants with PIL — each quadrant then fits vision_analyze cleanly
python3 -c "
from PIL import Image
im = Image.open('/tmp/sketch_300-1.png')
w, h = im.size
im.crop((0,0,w//2,h//2)).save('/tmp/sketch_q1.png')
im.crop((w//2,0,w,h//2)).save('/tmp/sketch_q2.png')
im.crop((0,h//2,w//2,h)).save('/tmp/sketch_q3.png')
im.crop((w//2,h//2,w,h)).save('/tmp/sketch_q4.png')
"

# 4. vision_analyze EACH quadrant separately with a focused extraction prompt
#    ("List ALL survey numbers visible, plot sizes, road names, north arrow, scale, legend")
```
- At 300 DPI the quadrants are ~2481x3508 px each — still large, but vision handles them; quadrants give far better OCR than the full page.
- Expect different quadrants to carry different signal: q1/q2 = title + roads + water body, q3/q4 = dense survey-number field + legend + north arrow + land-use table.
- **Check the "5-12 Model"-type filename trap:** the file name may say Sy 5-12 but the drawing shows the whole village (43-152 range). Never trust the filename for the survey-number list — extract from the drawing/table.

## 2. Stage-wise survey-number table (colour-coded stages)

Broker documents often break a parcel into **Stage/Phase 1-4**, each with its own sub-table: `Sl No | Sy No | Total Extent (A.G) | Karab | Net Extent | Present Owner | Father/Husband | Remarks`. The map page colour-codes parcels by stage (green/yellow/blue/purple) with a legend.

**Reconciliation pattern:**
1. **Sum every stage's TOTAL row** (extent A.G): Stage1 4A27G + Stage2 2A29G + Stage3 9A13.5G + Stage4 13A03G = ~29A 32.5G ≈ 30A.
2. **Add the sketch block** the file name refers to (Sy 5-12) — the sketch may carry the remaining ~10A → total reconciles to the claimed ~40A.
3. **State the math explicitly in the summary:** "table ~30A + sketch block ~10A = ~40A ✓" — this is the same claimed-vs-documented check as RTC reconciliation, just across document types.
4. **Flag remarks column:** "Conv." (converted land), "C & Govt" (government), and especially **"Court Stay"** — 2 Stage-3 entries with Court Stay = title risk, needs the order details before any deal.
5. **Multiple owners = list them all per stage.** A 40A plotted parcel across 4 stages can have 20+ distinct owners (Krupal & Others, V Rama, Gowramma, Dhyan Estates [a company], AM Amaranarayanaswamy, Muninarayanappa, Reddappa, Ramakrishnappa & Others, Manivenkatappa & others, Bachanma & Others, KM Anjinappa...). Present as a per-stage owner list, flag "& Others" entries and company owners — all must sign for a clean deal.

## 3. CDP zoning map — "is it zoned residential?"

Chikkaballapur / Bangalore CDP maps follow standard land-use colours: **yellow = residential**, green = parks/agri, red/pink = commercial/institutional, blue = water/tank, light purple = mixed/other residential.

- **Confirm the target village's colour directly** — vision_analyze the map asking "what colour is the zoning for village X?" Do not infer from the general legend if absent.
- Typical finding: "Arasanahalli is zoned YELLOW (residential); BOM Ring Road borders the south; tank to the SE; schools/colleges (B.G.S., Kempegowda, S.J. Tech) to the north" — the surrounding context (road access + anchors) doubles as a quick RD input.
- This maps to the Kelsa field `cf_land_zone` (Residential etc.) — cite the CDP map as evidence when filling it.

## 4. Land-use analysis table inside layout plans

Proposed layout PDFs often embed a land-use breakdown at the corner: `Total Extent: 11A-8G | Residential 24026.02 sqm 53% | Park 4680.71 10.33% | CA 2270.47 5% | Road 14346.96 24.87%`.
- Use it for: (a) confirming the layout's own arithmetic, (b) FSI/planning sanity, (c) noting the layout area may be a SUBSET of the full deal (11A-8G layout ≠ 40A total land — the rest is raw/other sy numbers).
- The layout's plot grid (9.20m x 12.20m ≈ 30x40 plots, 9m roads) + survey numbers (43/1, 44/2, 44/4, 47/1, 47/2, 47/4, 57/2A, 57/2B) feed `cf_land_sketch` and `cf_sy_nos`.
