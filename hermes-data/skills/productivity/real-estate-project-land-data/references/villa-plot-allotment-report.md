# Villa Plot Allotment Report — Worked Example (Ranka Oasis, Aug 2026)

Trigger: user sends a master plan PDF + inventory sheet (XLSX or live Google Sheet) + an investor list screenshot, and asks to "generate a report" that takes customer name/dimension/facing, goes to the master plan, marks plot numbers (or confirms they're marked), and gives one table describing all the shortlisted plots.

## Report shape (Bharat's expected structure)

1. **Investor / customer table** — name, amount, option (Villa / Buy Back), facing, villa size (SBUA). Exclude Buy Back investors from the allotment and mark them "Excluded (Buy Back)".
2. **Master plan — marked plot numbers** — list the shortlisted plots grouped by facing; include the annotated plan image; note which plots were already marked on the source PDF.
3. **Plot description table** — plot #, facing, corner, shape, E–W dims, N–S dims, area sqft, peripherals (East/West/North/South by).
4. **Proposed allotment matrix** — facing-matched: East investors → East plots, West investors → West plots, note spares and pending decisions (e.g. 1800 sqft plots reserved with Nishant).

## Workflow that worked

### 1. Read the inventory (both copies)
- Uploaded XLSX: `openpyxl.load_workbook(..., data_only=True)` — check EVERY tab (e.g. "Master Sheet " vs "As per sanction layout"). Sanction tab may use older numbering and omit plots added later.
- Live Google Sheet: `build_service('sheets','v4', service_name='google-draas')` + `values().get()` — verify the uploaded copy matches the live "area statement" sheet (Ranka Oasis: `1jHjOIUQSMVwVQewFES2d77D9SaHK2DcUbbTBvwwRH8o`).
- Pull only the target plot rows; print full row dicts including peripherals.

### 2. Locate plot numbers on the plan via pdftotext -bbox (reliable)
Whole-page `vision_analyze` returned only the GENERAL NOTES boilerplate. Use the PDF text layer instead:

```bash
pdftotext -bbox "plan.pdf" /tmp/plan_bbox.xml
# parse: <word xMin=".." yMin=".." xMax=".." yMax="..">TEXT</word>
```

Map PDF-point coords to rendered-image pixels:
```python
scale = image_width_px / page_width_pts   # A2 1191x1684pts @200dpi -> 3309px -> 2.778
img_x, img_y = int(pt_x * scale), int(pt_y * scale)
```

Then crop tight windows (±30-60 pts) around each target plot label and run `vision_analyze` on those crops for visual checks (marks, neighbours, roads). Confirmed this maps exactly: plot 105 label at x=602 → left column, 119 at x=632 → right column, matching inventory peripherals (105 "East by Plot 119").

### 3. Check for pre-existing hand marks
Ask vision on a zoomed crop: "Are any plot numbers circled or marked with thick black pen/pencil? List exactly which." Bharat had already circled all 9 chosen plots (105, 107, 109, 119, 118, 117, 92, 93, 95) — confirming his verbal list verbatim. Report this to the user rather than assuming you must mark the plan fresh.

### 4. Resolve facing + road side from inventory + plan text
- Inventory Facing column + Peripherals ("West by Road" etc.) agree with plan geometry.
- Roads visible in bbox text (ROAD K, ROAD M labels) confirm which plots front which road.

### 5. Flag stale dimensions instead of guessing
Plots 93/95/105/107/109 showed ~645–760 sqft while 92/117/118/119 showed ~1,490–1,520 sqft, yet the plan drawing shows the 105/107/109 column at the same width as 117/118/119. Since the plan is NTS ("Do not scale drawings"), drawing width is not proof — add a visible **Verification flag** box in the report and ask the user to confirm against the sanctioned layout. Never silently pick one source.

### 6. Generate the PDF (WeasyPrint)
- 4 sections as above, navy headings, tables with `border-collapse: collapse`, `Courier New` for amounts/areas, `@page A4 margin 55-60px`.
- Embed the annotated plan image (`img src=/tmp/...`), annotate with PIL red translucent rects + legend before embedding.
- Footer: "Draft for review; no allotment is final until confirmed."

## Pitfalls
- `pdftotext -layout` alone doesn't give coordinates — must use `-bbox` for cropping math.
- Vision width comparisons on NTS plans are contradictory; never use them to infer area.
- Hand-drawn circles interfere with pixel line-detection of plot boundaries — don't rely on automated boundary detection on a marked plan.
- The plan text layer has plot numbers and road labels but NO per-plot dimensions ("use figured dimensions only" → dims live in the inventory).
- "As per sanction layout" tab can be missing plots that the master tab has (Ranka Oasis sanction tab lacked 88–92 and 116–120) — master tab is the working source.
