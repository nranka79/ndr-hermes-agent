---
name: land-sketch-map-annotation
description: Annotate Indian village land sketches / joint maps (typically AutoCAD-exported PDFs) with survey parcels color-coded by category (sale deed vs agreement/GPA) — extract survey labels from the vector text layer, detect the map's own colored boundary strokes, recolor parcel boundary lines, add a legend. Use when the user says "mark these survey nos in this map" / "color the boundaries for sale deeds and agreements" on a village land sketch, joint map, or partition-deed map.
---

# Land Sketch / Joint Map Annotation

Trigger: user supplies a village land sketch, joint map, or partition map (PDF, often from AutoCAD / Photoshop) plus a list of survey numbers and asks to mark sale-deed vs agreement parcels, usually with different colors/patterns and a legend.

## Core workflow

1. **Check the vector text layer FIRST** — AutoCAD-exported PDFs almost always embed real text. `pdftotext -layout file.pdf -` gives survey labels (209/1, 221/2, 45/5B, 45/P3...) far more accurately than OCR. If the layout dump is dense, save it to a file and regex-extract `\d{1,3}/\d{1,3}[A-Za-z]*` tokens plus standalone parcel numbers (210, 223, 181). This is the authoritative label source; OCR is the fallback.

2. **Get exact label coordinates with PyMuPDF** — `page.get_text("words")` returns `(x0,y0,x1,y1,word,...)`. Build a label→center map for the survey numbers you care about. These coords are what you use to place markers/assign strokes. (venv note: pymupdf may live in a project venv like `/tmp/docenv/bin/python3`; check `find / -name pymupdf -maxdepth 6`.)

3. **Detect the map's OWN color-coded boundary strokes** — `page.get_drawings()` returns dicts with `color`, `rect`, `items`. Count stroke colors. In Byadarahalli's sketch: magenta/pink `(0.663, 0.325, 0.627)` = Satvik-owned parcels, blue `(0.478, 0.686, 0.875)` = other parcels. The map often already encodes ownership — reuse its stroke clusters to know which parcels exist even when unlabeled.

4. **Assign boundary strokes to parcels** — for each colored stroke, find the nearest survey label within a radius (~40pt of label center). Strokes whose nearest label is a sale-deed survey → recolor red; agreement survey → blue. Keep strokes with no nearby label in a candidate list — they may be an unlabeled parcel the user can identify (see pitfalls). ⚠ As of Aug 2026 the user wants LABEL-ONLY marking (colored boxes around labels), NO boundary-line overlays — skip step 5 unless explicitly asked.

5. **Recolor with vector overlay** (not pixel edits) — draw lines over the original strokes with PyMuPDF: `page.draw_line(fitz.Point(p1), fitz.Point(p2), color=..., width=2.2-2.4)`. Rebuild each stroke's segments properly (see the `l`-item pitfall below). Render final at 300 dpi for delivery. ⚠ Superseded by label-only preference for Prakash/DRA; keep for other clients who still want boundary lines.

6. **Add a legend** — always. Box + colored line sample + "SALE DEED (Registered)" / "AGREEMENT / GPA / ATS". Include sub-notes like "incl. 45/P3, 45/P5, 45/P7" when the user expands the category. Use fontname="helv" only (helv-bold may not exist in some builds → "need font file or buffer" exception).

7. **Embed the extent table ON the map** (Prakash/DRA requirement since Aug 2026, "PL ADD THE TABLE TO THE MAP ONLY") — build a SINGLE combined page: marked map stamped at top, table panel drawn below. See `references/map-with-extent-table.md` for the working composite recipe (separate-doc `show_pdf_page` trick, table layout, totals row). Do not ship the table as a separate file first.

8. **Verify by pixel sampling** — render PNG, then for each parcel's label box check dominant color (r>180,g<90,b<90 = red; b>170,r<90,g<130 = blue) at the label region. Catch silent misses before delivering. Also OCR-check the table panel totals.

## User preference (Prakash / DRA) — CRITICAL
## User preference (Prakash / DRA) — CRITICAL (updated Aug 2026)

- **MARK ONLY THE SURVEY NUMBERS with color code — NO boundary-line overlays.** An earlier session asked for "different colour lines of the boundaries", but that style was later explicitly REJECTED: "I M NOT HAPPY WITH THIS MARKINGS AND BOUNDARY LINES - JUST REDO AND MARK ONLY SURVEY NOS WITH COLOR CODE". The accepted style: draw a small colored filled box around each survey-number label (red = sale deed, blue = agreement), re-draw the label text dark on top, and draw nothing else over the parcel geometry. Do not recolor parcel boundaries.
- **Embed the extent TABLE ON THE MAP itself** ("PL ADD THE TABLE TO THE MAP ONLY"). Deliver ONE combined artifact: marked map on top, extent table panel below (single page). Do not first deliver the table as a separate file — the user rejected that flow.
- **Table shape:** two sections — LANDS UNDER SALE DEED and LANDS UNDER AGREEMENT TO SELL — each with per-row SL NO / SURVEY | EXTENT (A-G format) | RMK, a TOTAL row per section, and a GRAND TOTAL row. Extents from deeds/RTCs/partition deed; 1 Acre = 40 Guntas. Parcels whose extent includes kharab (221/2, 181) get a "K" mark; show net-of-kharab alongside the grand total. New agreement parcels not in the deed list (45/P3, 45/P5, 45/P7) take extent from the sketch's own extent tokens — flag that sourcing.
- **Always add a legend** with explicit color codes ("COLOR CODE - SALE DEEDS" / "COLOR CODE - AGREEMENTS").
- Deliver both PNG (for Telegram inline display) and PDF (for archive); the combined map+table PNG is the primary deliverable.
- When the user identifies an unlabeled parcel ("THE RED MARKED IS 190/3"), trust them and add the label — they know the land better than the map's text layer. If the user then says the auto-placed label is wrong, reposition using their verbal landmarks (e.g. "IT IS IN BETWEEN 19 and 223") — do NOT re-guess from stroke clusters.

## Pitfalls

- **PyMuPDF stroke extraction: 'l' items are endpoints, not standalone segments.** Most drawings have only `('l', Point)` items. A single-`l` drawing is a straight segment whose endpoints are the RECT CORNERS (`(rect.x0,y0)→(rect.x1,y1)`). Multi-`l` drawings are polylines — walk consecutive points. Extracting only the points and drawing consecutive pairs LOSES most strokes; the first attempt yielded 287 segments vs 1013 correct. Use the rect-corners rule for single-item drawings.
- **Labels can be missing from the text layer entirely** — 190/3 had NO `190` token anywhere in pdftotext output or full-map OCR, yet the parcel existed as pink strokes. When the user points at a red/pink-marked parcel, add the label at the unlabeled stroke cluster.
- **Some parcels have BLACK boundaries, not pink/map-blue** — 210 and 216/1 on the Byadarahalli sketch are drawn with black strokes. If you only recolor pink/map-blue strokes, these parcels get NO overlay (silent miss). Include black strokes in the per-segment assignment (R≈60, assign each segment by midpoint→nearest target label). Long black polylines crossing multiple parcels need per-SEGMENT assignment (not per-drawing), or their whole span gets one label's color.
- **`45/P3`-style labels break the default regex** — `\d{1,3}/\d{1,3}[A-Za-z]?` does NOT match P-labels (letter sits between slash and digit). Use `\d{1,3}/[A-Za-z]?\d{1,3}[A-Za-z]?` or search words containing `P` near survey clusters. P-labels were present in the text layer all along but missed on first pass.
- **Nearest-label assignment can drop strokes** when the true label isn't in your target set (e.g. strokes closer to a standalone "45" text than to "216/1"). Assign by "nearest among target labels within radius R", not "nearest label globally".
- **Adjacent parcels may share one stroke band** — e.g. 216/1 + 216/2 drawn as a single pink block with the label at the edge. If both are the same category, coloring the band once is correct; if mixed, flag it rather than forcing a split.
- **User phone screenshots of the map OCR terribly** (zoomed crops, stylized). Don't burn time re-OCRing them — use the vector layer + user's verbal identification.
- **PDF export can lose the table text even when the PNG is perfect** — composite pages built with `show_pdf_page` + vector `insert_text(fontname="helv")` on the same page export PDFs where the table renders as EMPTY colored boxes (`pdftotext` errors `Unknown font tag 'helv'` / `No font in show/space`; `pdftoppm`+vision shows bare rectangles). ALWAYS verify the PDF separately: `pdftoppm` → crop table region → OCR/vision. Fix: rasterize the table panel to PNG and stamp it as an image, or embed a real TTF fontfile. See `references/map-with-extent-table.md`.
- **User says "check the total (e.g. 42 acres)"** — recompute item-by-item (1 acre = 40 guntas) and reconcile against OTHER sources (Documents sheet etc.). Scope differences are normal: map table may exclude 41/11 (not drawn) and include 10A P-parcels; docs sheet may include 41/11 but exclude P-parcels and count ATS+GPA on the same survey once. Report both totals + the scope delta. See `references/map-with-extent-table.md`.

## Verification checklist before delivery
## Verification checklist before delivery

- [ ] All target survey labels found in text layer OR confirmed by user
- [ ] Sale-deed labels show red markers, agreement labels blue (label-box style for Prakash/DRA)
- [ ] Legend present with both color codes
- [ ] Extent table embedded ON the map (single page) with separate Sale Deed / Agreement sections + totals (Prakash/DRA)
- [ ] Unlabeled parcels the user identified (e.g. 190/3) have labels added AT the location the user specifies
- [ ] Pixel-sampled verification passed for each parcel region; table panel OCR-checked (totals)
- [ ] PDF re-rendered and table text verified present (PDFs can drop `helv` text — see Pitfalls)
- [ ] Totals cross-checked item-by-item and reconciled against other sources (scope deltas stated)
- [ ] PNG + PDF both saved

See `references/pymupdf-map-annotation.md` for the working extraction/recolor code recipe and the stroke-assignment JSON pattern.
See `references/map-with-extent-table.md` for the composite single-page map+table recipe, extent values table, and label-marker code (Prakash/DRA preferred deliverable).
See `references/partition-deed-schedule-reading.md` for partition cum settlement deed schedule anatomy (A/B/C), Clause III overrides, ocrmypdf + vision-verify recipe, and the Satvik SRJ/10373 worked example.

## Cross-referencing a partition cum settlement deed for extent sourcing

Extents for the table often come from a **partition cum settlement deed** (firm dissolution
between partners, e.g. Satvik Developers SRJ/10373/2023-24, Ashok Kumar & C.R. Nagendra).
When the user asks "which survey nos did X get" from such a deed, follow the schedule-reading
workflow in `references/partition-deed-schedule-reading.md` (in this skill). Key facts for map
work: Schedule C (minority partner) holds the parcels allotted to that partner; Schedule B +
all ATS/GPA/JDA and pending-registration rights go to Partner 1 (90% partner). Parcels already
marked sale-deed on the map (e.g. 221/2, 176/2) can still be the minority partner's share —
the schedule confirms post-reconstitution ownership, not the deed type.
