---
name: apartment-area-uds-statement
description: "Build unit-wise area / UDS statement spreadsheets for DRA apartment projects (Ranka Iris, Ranka Amber, Aquagreens, South City, etc.): source authoritative saleable-area + undivided-share data from the final OC, sanction plan, area-computation sheets AND the sale-agreement list, cross-check, and deliver a Google Sheet with per-row source links. ALSO the lookup/extraction home for the REGISTERED JDA AREA-SHARING / AREA-ALLOCATION AGREEMENT that fixes ratio, unit-wise allotment and parking for a JDA project (jda-area-sharing-agreement.md). Triggers: 'make a similar area spreadsheet for our apartments', 'unit-wise area statement', 'SBA and UDS per unit', 'registered area sharing / area allocation agreement', 'the sharing agreement for the JDA', 'area allocation agreement where the building is approved'."
version: 1.0.0
author: Hermes (DRAAS)
---

# Apartment Unit-wise Area & UDS Statement

Used when NDR asks for a structured spreadsheet listing every apartment in a DRA project with saleable area (sq ft AND sq m), UDS per unit, and a traceable source link for each figure — typically modeled on a template he shares (e.g. the Lotus Domlur area statement image).

## Source hierarchy (which number wins)
0. **REGISTERED JDA AREA-SHARING / AREA-ALLOCATION AGREEMENT — the top authority.** For any project
   developed on a JDA (landowner + developer), the executed **Sharing Agreement / Supplementary Sharing
   Agreement** registered against the Principal JDA is the instrument that fixes the saleable area, the
   50:50 (or other) ratio, the **unit-wise allotment**, and the parking split. Everything below — sale
   agreements, area statements, marketing collateral — should agree with it. Locate and read this FIRST
   when the user says "registered area sharing / area allocation agreement", "the sharing agreement for
   the JDA", or asks about allotment in a JDA project. Full lookup + extraction recipe:
   `jda-area-sharing-agreement.md`.
1. **SALE AGREEMENT list — the contract numbers.** For each project the definitive flat-wise SBA+UDS table usually arrives as an email table from the family/legal coordinator in the e-Khata / BBMP thread (e.g. Bhavik for Ranka Iris), often ending with "The above are the UDS mentioned in the sale agreements." Treat as AUTHORITATIVE for legal/contract deliverables.
2. **FINAL OC** — confirms unit count, which floors have units, per-floor built-up area (sqm), and amenity floors (club house/gym/MPH = 0 units). Scan → OCR with pdftoppm + tesseract when vision_analyze errors.
3. **Internal area-computation sheets** (AREA CHART, Floor Plan Area Computation, Area Calculation Details) — working basis (carpet/balcony/BUA/common/SUBA). Often DIFFERS from agreement figures — use for context/backfill only and flag the discrepancy to NDR.
4. **Sanction plan** — plan-sanction No./date for the header block.

## Steps
1. Drive search `name contains '<Project>'`; the Customer Legal Set / OC-application folder is the first place to look (holds OC, AFS, Deed of Declaration).
2. Download + OCR the FINAL OC (filename usually contains 'OccupancyCertificate'); extract unit count, floors, per-floor built-up.
3. Export the area-computation spreadsheets via Drive export_media (xlsx) and read with openpyxl.
4. Gmail-search the e-Khata/BBMP thread for the flat-wise SBA+UDS table: `"Ranka Iris" "1001"` or `"Ranka Iris" "area statement"`. Pull full text with format='full' and walk parts for text/plain body (the table may be in the BODY, not an attachment).
5. Read contract docs (Proforma AFS / Sale Deed draft) for Schedule B wording (SBUA + UDS %) and exclusive-terrace clauses (e.g. Ranka Iris Flat 1301 terrace).
6. Build the Google Sheet:
   - Tab 1 "Area Statement": title block (project, OC No/date, sanction No, note row for amenity floors), then Sl / Flat / Floor / SBA sqft / SBA sqm / UDS sqft / UDS sqm / UDS % + per-row `=HYPERLINK(...)` to the sale-agreement source; Totals row.
   - Tab 2 "Sources": doc table with links + what each provides, plus an OC floor-wise cross-check table.
7. Name per convention: `YYYYMMDD_<Project>_AreaStatement_UnitWise_SBA_UDS`; file in the project's Customer Legal Set folder. Set 30-day viewer access per NDR preference.

## Pitfalls
- **A registered SSA's stated TOTAL can exceed the sum of its own Schedule B unit rows — flag, don't fix.** Ranka Amber: Sch B per-side 11,976.00 sq ft × 2 = 23,952, but Clause 5 states total saleable 27,544.00 sq ft. The gap is the omitted balcony / common-area loading columns. Report both figures with their basis named; never silently reconcile.
- **Unit floor labels disagree between the registered SSA and the marketing/customer area statement.** Amber carries three schemes at once (SSA: LO on Ground + Third; area statement: 201-205 on Second, LO on Fourth; internal strata: LO 001-005 + 301-305). The registered instrument governs. Surface the conflict — do not renumber anything yourself. Details: `jda-area-sharing-agreement.md` §5.
- **`fullText` hits are a discovery net, not evidence.** Queries like `fullText contains 'area sharing'` return every IRR model, DPR and enterprise-data sheet that mentions the phrase. Confirm any hit by reading the document before reporting it. Also: the area-sharing agreement is titled **Supplementary Sharing Agreement** — a `name contains 'area sharing'` search returning ZERO is expected, not a miss.
- **Villa/plotted master inventories carry MULTIPLE area variants** (Oasis master sheet runs per-plot FSI and SBUA under Grove 1.75 / Vista 1.8 / Reserve 1.85). Pick the variant matching the project's approved FAR (Oasis FAR 1.8 → Vista), state the choice in a note row, and leave the other variants referenceable — do not silently pick or merge them.
- **Approved-plan aggregates vs per-plot sums often disagree — flag, never "fix".** The DTCP/TNRERA approval letter (Oasis, dt 13.01.2026) says residential house sites total 10,193.49 sq.m for 130 sites, while the sum of transcribed per-plot areas is 17,372.66 sq.m. A scanned approval letter usually carries ONLY aggregate stats (the map shows dims only) — there is no per-plot table to transcribe. Record BOTH figures on the sheet (per-plot rows + a note quoting the letter) and surface the gap to the user; it needs a surveyor, not a spreadsheet edit.
- **Sanction-layout transcription tabs can be incomplete** (Oasis `As per sanction layout` drops plots 116-120 and has no area column). Fall back to the working Master Sheet tab for the missing rows and mark the row source; filter out merged/alternate plot rows ('79-"80"', '113-114-"115"') by accepting only plain numeric plot numbers.
- **Google Sheets API: rename/add tabs BEFORE values().update using A1 ranges.** New spreadsheets start with a tab literally named "Sheet1" — if you reference `Area Statement!A1` before renaming, you get HTTP 400 `Unable to parse range: Area Statement!A1`. Do `updateSheetProperties` (rename sheetId 0) + `addSheet` in one batchUpdate first, then write values.
- **Build scripts that crash mid-way leave partial spreadsheets on Drive.** Make the script idempotent: delete any partial ID from a failed run at the top, then recreate. Always verify parents + contents after.
- **Google Docs export fails with 'file too large to be exported'** (exportSizeLimitExceeded, common on big Deed/Declaration drafts) — use Docs API `documents().get()` and join paragraph text instead. Native .docx gives 'fileNotExportable' — use `get_media` + unzip `word/document.xml`, strip tags with `</w:p>` → newline.
- **UDS % basis:** compute against the TOTAL UDS pool (sum of agreement UDS, e.g. 10,538.28 sqft), NOT the plot area; keep header and formula consistent (hit this mid-build).
- **openpyxl missing in /opt/hermes/.venv and pip is absent:** `uv pip install --python /opt/hermes/.venv/bin/python3 openpyxl` (uv is the package installer on this box).
- **0/0 amenity rows:** OC shows first floor = gym/MPH with no residential unit → include the flat as 0 SBA / 0 UDS with a note; don't delete it.
- **Uploaded "floor plan" PDFs are often MEP/consultant layouts with NO area annotations — verify before promising extraction (2026-09-21, Ranka Iris).** A DHCES "Even Floor Plans" sheet (RI-PL-PLN-301-R0, "TYPICAL FLOOR 4th/6th/8th/10th/12th") for Ranka Iris was a *plumbing layout*: the text layer carried room labels (Master Bedroom, Bedroom 02/03, Living, Dining, Kitchen, Balconies 02–04, Utility, Servants Room, Walk-in WR, Powder Room, Lobby, 4 toilets) plus a fixture mounting-height schedule — but ZERO carpet/BUA/SUBA figures. Never assume a plan sheet carries areas. Verify in three cheap passes before deciding you can extract:
  1. `pymupdf page.get_text()` — grep for `sq.ft|sqft|sqm|carpet|built|super` (also dump all spans containing digits with positions; pipe sizes 75/110/630/758/1108 and mm heights 400–2050 are plumbing annotations, NOT areas).
  2. `pdftoppm -png -r 300` + tesseract full page.
  3. Zoom-crop the drawing region (~150% LANCZOS crop) + OCR again.
  If no area figures exist on the sheet, say so plainly — do not invent areas from the layout — then supply the authoritative numbers from project records (sale-agreement SBA+UDS list; AREA CHART for carpet/balcony/BUA/common/SUBA), and state the drawing confirms only the room configuration. The drawing title block is the tell: plumbing/MEP planners (DHCES, "MEPF CONSULTANTS") draw fixtures, not area schedules; an architectural plan set or an area-computation sheet is where areas live.

## Ranka Iris worked example
(Ranka Iris worked example previously here was removed 2026-10-21 — project closed, OC issued.)

## Verifying sheet state & history before editing
When a sheet is said to "need updating", establish the ground truth first — what the live
sheet holds, whether the user (not you) changed it, and what a user edit actually changed:
`sheets-revision-forensics.md` (Drive `revisions()` list + per-revision xlsx
export, stdlib xlsx/cell parsing without openpyxl, and the "empty diff = formatting-only"
finding). Then diff the sheet against the source document and report the real gap — the
gap is often missing COLUMNS rather than wrong values.

## Two-source comparison sheets (Master Inventory vs Sanction/Approved — per-plot)

When the same inventory exists in TWO tabs/versions (verified 2026-09-10 on Oasis:
`Master Sheet ` working tab vs `As per sanction layout` dims-only tab) and the user asks
for "the difference of everything", build a **comparison tab** instead of editing either
source:

- One row per plot; columns: Master (facing / corner / shape / E, W, N, S dims) + Sanction
  (shape / dims) + a per-dimension **OK/DIFF** flag + Remarks column.
- **Dim equality needs a tolerant numeric compare, not string equality.** Dims come as
  expressions like `(15.85+2.1)` or `6.86+2.08`; parse via `eval_dim()` (strip spaces +
  parens, split on `+`, sum; plain decimals as-is) and compare with ~0.01 m tolerance;
  fall back to normalized-string equality for unparseable cells.
- **Δ Area column:** sanction tabs usually carry dims ONLY (no areas). Compute
  `area = ((E+W)/2) × ((N+S)/2)` from EACH side's dims with the SAME formula and show
  Δ = Master-calc − Sanction-calc (sqm + sqft). Same formula both sides isolates genuine
  dims differences from formula error; identical dims → 0. Highlight the Δ columns
  (yellow fill + bold). Explain in the reply that Δ is dim-derived, not an official area.
- **Filter to plain numeric plot numbers** (`str(p).strip().isdigit()`); merged/amalgamated
  rows ('79-"80"', '113-114-"115"') get a note, never compared.
- **Sheets API read-back returns STRINGS** — a plot column validates with
  `.isdigit()`, not `isinstance(v, int)`; a tally loop that filters on int silently
  reports 0/0/0.
- **Totals by plot range** (registered count 1–130 vs extra plots 131–138) — report
  separately, don't merge; also answer explicitly whether a headline total includes the
  extras (the ~17,372 sq.m question).
- Deliver the tally (e.g. 80 OK / 45 DIFF / 13 not-in-sanction) + the net Δ. Never
  auto-sync one tab to the other: flag the authoritative source (the sanctioned/approved
  plan) and ask.
- **Facing on the 'DTCP Approved Plan (13.01.2026)' tab**: the letter-size DTCP approval
  print carries NO facing labels and NO north arrow (verified 2026-09-11, Oasis) — facing
  is derived road-frontage, north-up. Don't re-derive a 130-row table from the tiny print
  (vision flips sides); block-verify instead. See `real-estate-project-land-data` →
  `oasis-plot-facing-sanction-verification.md`.

## Plot-area-sheet vs aggregate-statement reconciliation (Ranka Udaya pattern, 2026-09-11)
When the user supplies TWO plot-area documents — (1) an approved plan drawing / DTCP permission letter carrying ONLY an aggregate area statement, (2) a per-plot area sheet (Plot # / Length / Breadth / Area sqm / Area sqft / Facing) — build a nomenclature workbook with: Nomenclature tab (per-plot area sqft+sqm), Physical Area Statement tab (title block + area statement table from the letter/drawing + reconciliation note), Approved Layout Plan tab (verbatim per-plot sheet, full precision — do NOT round sft values, the source carries 9-decimal numbers), Plotwise Comparison tab (per-plot: stated area vs L×B-derived, Δ sqm, Δ %, flag rows where |Δ|>2%).
- **The sanctioned net plot area often EXPLAINS the gap**: per-plot sum + 10% OSR + utility = sanctioned net plot area (Udaya: 4,050.71 + 452.91 + 25.47 = 4,529.09 ≈ 4,529.14; the DTCP letter states road 2,546.86, public purpose 31.34 (0.69%), TANGEDCO 25.47 (0.56%)). State this as the reconciliation; never auto-fix.
- DTCP letter (Planning Permission) is a separate PDF from the drawing — pull BOTH from Drive (search `name contains '40623'` / 'Approved Layout Plan'); the letter carries the lot numbers (LP/HNTDA(SWP) No + PP (SWP) No) and 'ALLOTMENT DETAILS OF APPROVED LAYOUT PLAN' block.
- File naming: `YYYYMMDD <Project> Unit Nomenclature – Phase I`; place in the project's main Drive folder.

## BBMP / GBA bulk unit-new-khata application workbook (Ranka Iris pattern, 2026-09-17)

When the ask is "generate a template of data to be filled for applying individual khatas for each apartment
in bulk, to be issued by the GBA" — same unit-wise data class, different deliverable: a **portal fill-order
workbook**, not a Drive area statement. Mirror the portal's own section/field order and mark every value that
cannot be sourced from OC/CC/plan as a RE-collect cell. Full screen model, exact unit-form field list, the
date rule, and the Ranka Iris values: `bbmp-gba-bulk-khata-application.md`.

- **Regenerate, don't surgically edit.** Build these from a generator script (`document_cache/<project>/
  build_fill_sheet.py`) and make every revision a SCRIPT patch + re-run. openpyxl-editing the produced .xlsx
  in place risks dropping the embedded portal screenshots, fills and merged note rows, and destroys
  reproducibility. Copy the existing .xlsx to `/tmp` as a backup before rebuilding.
- **openpyxl round-trips silently drop embedded images when Pillow is absent from that venv** — the save
  succeeds with zero images and no error. Install the missing half rather than switching venvs:
  `uv pip install --python <venv>/bin/python pillow`. (`/opt/hermes/.venv` has Pillow but not openpyxl; a
  purpose-built workbook venv typically has openpyxl but not Pillow.)
- **Verify a rebuilt workbook from the zip**: count `xl/media/imageN.png` before vs after (e.g. 6 screens → 10
  after adding 4 close-ups) — that is the only reliable proof the screenshots survived — then read headers and
  values back with openpyxl. openpyxl writes inline strings, so there is **no `xl/sharedStrings.xml`**; grep
  `xl/worksheets/sheetN.xml`.
- **Ordinal QA:** `f"{n}th"` renders "2th / 3th Floor". Use a real ordinal helper. Cosmetic, but these
  workbooks are read by banks and BBMP staff, and Prakash is particular about the document surface.
- **The unit form carries ONE date field** (`Construction Completion Date`, dd/mm/yyyy) — there is no
  construction *start* date, so never carry a start-date column from the CC into a unit table.

## Unit-type comparison sheets (Ranka Iris pattern, 2026-09-21)
When the ask is "comparison of area figures across all unit types" for a project where several
spreadsheets carry different figures, build a **unit-type × source matrix** rather than another
flat list:
- One row *per (unit-type × source)*; columns: Carpet / Balcony / BUA / Common / Terrace / SUBA·SBA / UDS / UDS% / Notes.
- Unit types emerge from the agreement list + OC: Ranka Iris = EVEN (1002-1012, SBA 3774.81 UDS 880), ODD (1003-1011, SBA 3755.67 UDS 876.38), TOP 1013 (agreements treat it as odd but AREA CHART adds terrace 2119.24 → SUBA 4572.635; 2016 UDS tab uses BUA 4250 → 11.96%), AMENITY 1001 (0/0).
- Sources differ in REAL ways — surface them, never reconcile silently: agreement SBA (3774.81/3755.67) vs AREA CHART SUBA (3513.015) vs Costsheet (3500.278) vs Area Calc Details (3515.942) vs FloorPlan Sheet2 (3479.709) vs FAR sellable (3355.386); common share varies 656.60 → 797.27; carpet interpretations vary (2240.06 excl balcony vs 2602.76 incl balcony vs 2465.53 vs 2500.68).
- A room-level (L×B) "Area Computation" draft (2013-08-01) is design working, NOT unit totals — include in Sources tab with a "do not use" note.
- **Percent cells get eaten by the blanket `#,##0.00` number-format batch.** Apply the number format only to the ft² columns; give the UDS% column its own `PERCENT 0.00%` repeatCell (or write decimals). Otherwise "8.35%" displays as "0.08" and you catch it only at readback.

## Verification
After build: read back both tabs via Sheets API, confirm totals (SBA total, UDS pool = 100%), confirm file parents = intended folder, confirm per-row hyperlinks rendered in the Source column.