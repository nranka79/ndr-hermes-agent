# Per-plot area / facing extraction from AutoCAD-origin layout-plan PDFs

Worked 2026-09-11 on **Oasis Master Plan 03.08.26-Sheet 1** (Producer `pdfplot16.hdi`, Creator
`AutoCAD 2022`, A2 `1684x1191 pt`, `Page rot: 270`) → per-plot areas written to a new workbook tab
with a reconciling total. Reuse for any "add the areas of each plot from this plan" request.

## 1. Check the text layer FIRST (even if pdftotext looks like a jumble)

AutoCAD-exported layout PDFs almost always embed REAL text (plot numbers, areas, road widths) even
though `pdftotext -layout` may come out as one confusing wide column. The words ARE there with
x/y coordinates — that's a rotation/ordering artifact, not missing text.

```python
import pymupdf
doc = pymupdf.open(path); page = doc[0]
words = page.get_text("words")          # x0,y0,x1,y1,word,block,line,word_no
```

## 2. Token classes

- **Plot labels**: pure ints (`1`..`200`) OR dash tokens: `79-80` (range), `121-` `123-` (continuation),
  `113-114-` (multi-continuation → combined plot).
  Regex: `\d{1,3}` / `\d{1,3}-\d{1,3}` / `\d{1,3}-`.
- **Area tokens**: `\d{2,5}\.\d{2}` in the 400–12000 range (plans print areas in SQFT — 141 sqm
  std plot prints as `1517.71`).
- **Distractors to filter**: dim text pieces (`100 x 450 mm Kerb Stone` → int 100), road-width
  decimals (`0.800`, `0.942`, `4.600`, `0.962`), survey numbers (`158/1C9A`).

## 3. Coordinates-based pairing (nearest-neighbour on word centers)

Areas normally sit **~5–30 pt above/below the plot label** in text space. Assign each area token to
the nearest label within ~75 pt radius, then review: (a) labels with NO area, (b) labels with 2+
nearby areas, (c) big outlier distances. The first "dx/dy window" heuristic (e.g. `|dx|<30, -55<=dy<=12`)
tends to MISS valid pairs whose spacing is larger — global nearest-neighbour with a generous radius
then candidate review worked better.

## 4. Merged-token pitfall (critical)

The text layer can concatenate two adjacent numbers WITHOUT a space:
`1865.761092.74` = TWO areas (1865.76 for plots 79-80 + 1092.74 for plot 81).
Detect with regex for `\d+\.\d{2}\d+\.\d{2}`, split after the second decimal of the first number,
inject both as separate area tokens, then re-run pairing.

## 5. Combined plots and shared single areas

Master plans amalgamate sanctioned plots into bigger saleable plots: `79-80`, `82-83-84`, `85-86`,
`93-94` … `127-128-129-130`. One combined label → one area. Multi-label groups can still share ONE
printed area: Oasis labels `99-100` and `101-102` with a single `2219.55` sqft covering all four
plots. **Infer coverage by sum-checking against the sanctioned per-plot areas** (99+100+101+102 =
206.2 sqm = 2219.6 sqft ✓).

## 6. Plans omit areas for some plots — never invent

Oasis plan prints NO area for plots 6, 7, 8 (big plot + neighbours) and 131–138 (labels exist, no
area). Fill 6/7/8 from the sanctioned tab with an explicit "not printed on plan" note; list 131-138
as no-area rows, exclude from totals, explain in notes.

## 7. Verify ambiguous clusters with a vision pass

After pairing, render the page ONCE at good DPI (see §8) and ask the vision model (Gemini pool keys
work — see ocr-and-documents `references/vision-provider-fallback-ladder.md`) to confirm the exact
plot↔area pairs in the tricky regions (combined-label clusters, top-right corners, merged tokens).
"79-80: 1865.76", "81: 1092.74", "82-83-84: 1627.32" etc. came back clean and matched the sums.

## 8. Rendering: prefer pymupdf over pdftoppm for AutoCAD/PDFlib files

`pdftoppm` spewed hundreds of `Syntax Error (NNN): Bad block header in flate stream` lines on the
AutoCAD `pdfplot16.hdi` file and still produced the render. Use pymupdf:

```python
pix = page.get_pixmap(matrix=pymupdf.Matrix(200/72, 200/72)); pix.save('page.png')
```

## 9. Reconciliation closes the loop

Sum printed sqft → sqm (÷10.7639). Oasis: printed sum 16,311.37 sqm, and the ONLY gap vs the
sanctioned tab total 17,372.66 sqm was exactly plots 6/7/8 (778.69 + 145.27 + 137.28 = 1,061.24 sqm)
→ 17,372.70 ✓. A gap exactly equal to the no-area plots is proof the extraction is complete.

## 11. No-vision label search: keyword-scoped word dumps (identify amenities/clubhouse/commercial when vision is down)

Verified 2026-09-16 (Oasis master plan, vision_analyze 503 + no gemini keys). AutoCAD plans embed the answers in the text layer — you can locate ANY annotation class without a vision model:

1. `words = page.get_text("words")` (pymupdf coords are the UNROTATED page space — see §8 note).
2. Keyword sweep: `for w in words: if any(k in w[4].lower() for k in ['club','commerc','amen','shop','park','play','pool','gym','osr','pump','substation']): print(coords, word)`.
3. For a numbered block (e.g. plots 131–138), dump ALL words inside the zone rect `(x0,y0,x1,y1)` sorted by `(y, x)` — the surrounding road-section labels (`Plot Footpath Planter Carriageway`, `ROAD`, area tokens like `1517.71`) fall out and tell you whether the plots are road-served residential or labelled amenity land (no 'Clubhouse'/'Commercial' token inside = plain numbered sites).
4. Association trick: an annotation sits by the area token whose value matches its footprint — "1517.71 Clubhouse" = the Clubhouse label next to a standard 141 sqm plot's area; plot 6 (8,382 sqft vs 1,517 standard) is thus the big NE site hosting the clubhouse belt.
5. Caveat: clubs/pools/play-areas are usually drawn as UNLABELLED hatched shapes with only a text label nearby — the word dump proves presence + location band, not precise polygon ownership. State it as approximate and verify on a full-size drawing when possible.

Do NOT trust pdftotext -bbox coordinates for crops when the page has /Rotate (rotation 270): bbox (xMin,yMin) ≠ pymupdf (x0,y0) — they differ by the rotation transform. Build crops with `page.get_pixmap(clip=Rect(...))` using pymupdf word coords directly (clip is in unrotated space, pymupdf applies rotation internally).

## 10. Deliverable shape

New tab: title row → source row (plan file, units, date) → header
`Plot (as per plan) | Individual plots covered | Area (Sq.ft) | Area (Sq.m) | Notes` → one row per
plan label (combined labels as printed, coverage column listing sanctioned plot numbers) → TOTAL row
(sqft + sqm) → notes block (units, combined-plot mapping, no-area plots, sanctioned reference).
Format: bold title/header/total, number format `#,##0.00`, USER_ENTERED writes.

## Facing (same class of task)

A letter-size DTCP **approval letter print** (Producer `Microsoft Print To PDF`, `Page rot: 90`,
vector-outlined text — pdftotext empty, only a tiny 201x201 embedded logo) contains the approval
details + a small plot layout + a land line diagram, but **NO north arrow and NO facing labels**.
Per-plot facing must be DERIVED from road frontage (north-up). Do NOT attempt a full per-plot
facing re-derivation from such a tiny print: the vision model flips frontage sides for the same
plot across zoom passes (plots 74/86/87 read Left in one pass, Right in another). Keep the
master-derived facing values, verify at BLOCK level (entry road South → plots 6-8 South; middle
10.00m road → 56-62 North; internal 9.00m roads → strip pairs 81-86 East / 87-92 West, 93-102 East /
103-115 West; top-right 7.20m roads → 116-130), flag the ambiguous handful, and record the
derivation as a note row on the sheet. Only a full-size layout drawing settles the fine print.