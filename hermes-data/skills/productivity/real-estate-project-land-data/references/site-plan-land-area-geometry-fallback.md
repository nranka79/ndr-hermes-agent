# Site-Plan Land Area — Geometric Fallback (no printed area schedule)

Worked 2026-09-23: PRJ_0987_21-22.pdf (Ranka NorthStar, Allalasandra, Sy.No.14/1 khata 591/1077/14/1/1, BBMP ward 04). User shared a
screenshot of the SITE PLAN (page "1 / 5" in the viewer) and asked "get the total land area as per the land boundary".

## The problem
BBMP sanctioned site plans often carry boundary DIMENSIONS but NO printed "total site area / extent" figure anywhere
(text layer, title block, or area statement). On PRJ_0987 the text layer is ~13.7k chars of approval conditions +
joinery schedule — zero area figures except FAR-boilerplate mentions. So the total land area must be COMPUTED from the
boundary polygon.

## Key discovery: the screenshot's page is raster; another PDF page has the same drawing as vector TEXT
- Page index 0 (= viewer page 1/5, the SITE PLAN the user screenshotted): boundary dims are vector OUTLINES —
  `get_text()` finds none of 60.18/85.01/32.14... but the drawing renders identically.
- Page index 1: the SAME site plan drawn natively — `page.get_text("words")` returns every dimension with exact
  coordinates. **Always download the full PDF and check every page for the vector-text version** before trusting
  vision/OCR on the screenshot.
- Lesson: on PRJ/0987 the title-block area-statement TABLES are AutoCAD graphics (not text), but the drawing
  DIMENSIONS on page 2 ARE real text. The old "no area numbers in text layer" note applies to the tables, not the dims.

## Workflow
1. **Locate + download the PDF from Drive** (session_search found it: `PRJ_0987_21-22.pdf`, drive id
   `111Xbk0djC0PTdPHMy1oi4SEtNYb4aOmg`, folder "Old sanction Plan North Star"). Download via
   `drive.files().get_media(fileId=...)` + `MediaIoBaseDownload` (works fine for psingh's own-token session).
2. **Find the vector-text page**: loop pages, `page.get_text("words")`, look for the boundary dim strings
   (60.18 / 85.01 / village-chain numbers). That page is the geometry source of truth.
3. **Extract dimension labels + positions**:
   ```python
   words = page.get_text("words")  # x0,y0,x1,y1,word,...
   # match tokens: top 60.18 / 85.01; bottom chain 14.74,4.65,32.14,3.15,7.75,3.42,1.90,39.42,0.28,19.08,1.17;
   # left 30.91; right 39.53 (+ road widths 10.50M / 11.80M, 30M lake buffer)
   ```
4. **Calibrate scale from an annotated full-edge dimension** (don't assume PDF pt = drawing scale):
   top boundary line (1394.1,732.4)->(4553.2,738.1) = 3159.1 pt; dims 60.18 + 85.01 = 145.19 m
   → **21.758 pt/m ; 1 pt = 0.045959 m**. Boundary chain: bottom village boundary 14.74+4.65+32.14+3.15+7.75+3.42
   +1.90+39.42+0.28+19.08+1.17 = 127.70 m.
5. **Area via raster flood-fill** (vector graph-walk failed — see pitfalls). Render the SITE-ONLY region at high dpi
   (`get_pixmap(dpi=150, clip=...)`), binarize (<128), flood-fill 4-connected from window border = "outside",
   count unvisited = enclosed land (property loop interior incl. building footprint).
   - SELF-CALIBRATE px/m within the SAME render: measure the top boundary line's pixel span against 145.19 m
     (do NOT reuse a px/m from a different page — page 1 vs page 2 renders have different scales/positions).
   - Result: **~4,830–4,834 sq.m ≈ 52,000 sq.ft ≈ 1.19 acres ≈ 1 acre 7.8 guntas** (flood-fill estimate — flag as
     estimate, not a printed figure).
6. **Report honestly**: state that the plan has no printed total-area figure, your computed estimate, the method
   (boundary dims → polygon → scale-calibrated), and offer cross-check via DRAAS land records (Ranka NorthStar
   JDA/Title Report; earlier survey figure was 4,173.25 sqm for Sy.No.14/1 — plan boundary may differ).

## Pitfalls (all hit in this session)
- **CAD export duplicates every line 2–4×** (same segment listed with tiny dx/dy variants). Graph construction +
  contour-walk from `get_drawings()` breaks: nodes fork at corners, walker dives into the building outline or loops
  between parallel duplicates. Don't burn iterations on vector contour walking — go raster flood-fill.
- **Whole-sheet renders pollute the flood fill**: page 2 also contains the basement floor plan + joinery schedule
  tables; a window flood-fill over the whole sheet counts table interiors/enclosed rooms as "land". Crop tightly to
  the site-plan bbox first (use the dim-label coordinate bounds as the window guide).
- **Vision OCR on zoom crops is not reliable for drawing dims** (read "65.0 | 60.15 L", "52.14", "BASEMENT FLOOR
  PLAN" inside the site-plan crop). Use pymupdf text layer when it has the numbers; use vision only for layout
  orientation / confirming which drawing is which.
- **Page scale differs between PDF pages**: p0 site window vs p2 site window gave wildly different px/m if you
  assume one calibration. Always calibrate per render.
- **entity_resolver may be down** (TypeError `_handle() got an unexpected keyword argument 'task_id'`) — don't hold
  up the task; note the cross-check is pending and proceed with geometry.
- The top boundary label OCR'd as "PROPERTY IN SY.NO.14/2" in the screenshot but the PDF title block says
  "SY.NO.14/1" — trust the vector title block, not screenshot OCR.