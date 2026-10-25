# TN-RERA buyer-cost price list structure (villa vs plot) — verified statutory components

Worked 2026-10-09: "Ranka Oasis price list for VILLA + Ranka Udaya price list for PLOT, with all
components the customer incurs as per TN-RERA norms." Deliverable = Google Sheet, 3 tabs
(per-project price list + statutory basis tab), anyone-reader link.

## Where the numbers come from (source hierarchy — never invent a rate)
- **Plot per-sq.ft rate:** the project's official COST SHEET (e.g. Ranka Udaya `Ranka_Udaya_Cost_Sheet`
  = ₹4,000/sq.ft) — NOT memory, NOT portal listings, NOT a single executed deal. Executed
  agreements may be at a discount (Udaya Plot 31 = ₹33,00,000 for 1,236 sq.ft ≈ ₹2,670/sq.ft,
  sold 2026-10) — that is an actual transaction datapoint, worth flagging to the user, but the
  LIST is built on the approved cost-sheet rate unless told otherwise.
- **Per-plot area:** the approved-layout plot measurement sheet / ICICI unit nomenclature PDF
  (plot no, side, frontage, depth, area sq.m + sq.ft, type). Udaya: 38 plots, right side 1–19
  (1,025–1,199 sq.ft), left side 20–38 (1,181–1,260 sq.ft), two corner/bottom irregularities per side.
- **Villa variants + size:** internal planning/line-value sheets (e.g. Oasis East/West/North —
  3 BHK, plot 1,566.67 sq.ft, BUA 2,493 / 2,351 / 2,174 at ~₹12,000/sq.ft built-up). If the
  villa rate is from an internal working sheet, mark it "internal — confirm with Management";
  flag that it is not a published rate card.
- **Allotment letter / agreement drafts** confirm charge structure ("exclusive of GST, stamp duty
  and registration charges") and payment milestones, but leave the consideration blank — do not
  quote a price from a blank field.

## TN statutory components (verified against IGR TN fee schedule, 2026)
| Component | Rate / basis |
|---|---|
| Basic sale consideration | Plot: ₹/sq.ft × area; Villa: ₹/sq.ft BUA × BUA |
| Stamp duty (conveyance) | 7% of consideration / market value, whichever higher |
| Registration fee | 4% of consideration (IGR TN) — combined with stamp ≈ 11% |
| GST | Plots/land sale: EXEMPT. Under-construction villa: 5% without ITC on construction value; land 1/3 abated → effective ~3.33% of basic. No GST once OC/complete. |
| TDS u/s 194-IA | Buyer deducts 1% on consideration ≥ ₹50 lakh; shown as a note, not a cost line |
| RERA advance cap | Promoter cannot take >10% before registered Agreement for Sale (s.13) |
| RERA escrow | 70% of collections into separate project account (s.4(2)(l)(D)) |
| Legal / documentation | Fixed lump (Udaya cost sheet: ₹50,000); villa estimate higher (~₹1.5 L) |
| Booking / schedule | Udaya cost sheet: ₹5,00,000 at booking, min 20% at agreement (within 15 days), balance in 30–45 days |
| Maintenance / AMC | Villa community deposit + monthly AMC; plots pro-rata common-area upkeep |
| Other | Power/water connection, bank processing if financed, society corpus, POA — as actuals |

Important note for the sheet: stamp duty is on the HIGHER of agreement value / guideline value —
for Hosur-belt plots the guideline value can exceed the asking rate; flag that totals are
estimates and the Sub-Registrar figure governs. Women-buyer concessions (TN, ≤₹10L only) do not
apply at these values.

## Build shape that worked
- **TWO variants — pick per the ask.** (a) STATIC: compute every money column in Python (rounded
  ints) then `values().update(..., valueInputOption='USER_ENTERED')`. (b) EDITABLE/LIVE — what
  Prakash converged on ("update the sheet with editable formulas, if I change the base price then
  other charges to be updated as well"): write FORMULAS, not values, so a rate change reprices
  every row. See § Editable rate-card variant below; prefer (b) for any price list he will quote from.
- Headers with "(Rs)" in the label text; body cells pure numbers; format `#,##0` (type NUMBER).
  See `gws-automation` → `references/sheets-values-write-number-format-pitfalls.md` for the
  RAW-vs-USER_ENTERED and currency-pattern #VALUE! traps.
- 3 tabs: `Oasis - Villa Price List`, `Udaya - Plot Price List`, `TN-RERA Statutory Components`.
- Freeze header row, navy header fill, column widths, then `permissions type=anyone role=reader`.
- Verify by re-reading FORMATTED_VALUE (e.g. `29,916,000` not `#VALUE!`).
- Backup interrogation of project data: Oasis investor-costing sheet lives under NDR's account —
  a session token that cannot read it should NOT switch to DWD; fall back to internal working
  sheets already visible to the session user and label the source honestly.

## Editable rate-card variant (live formulas + parameter block) — verified 2026-10-13
Prakash's ask: "add formulas to edit the base price and get the cost" → "if I change the base price
then other charges to be updated as well". Shape that works:

- **Parameter block at the TOP-RIGHT (Q2:R7), yellow-filled**, one cell per driver:
  `R2` villa/plot rate ₹/sqft · `R3` stamp % · `R4` registration % · `R5` GST % · `R6` legal lump ·
  `R7` SBUA option selector (`Gro`/`Vis`/`Res`). Labels in Q. Title the block so the user sees it.
- **Every money column is a formula referencing the params with absolute refs**, e.g.
  `=ROUND(H5*$R$2)` basic, `=ROUND(J5*$R$3)` stamp, `=$R$6` legal, `=SUM(J5:N5)` total.
  Rate column itself `=$R$2` so it visibly tracks the param.
- **SBUA option selector** for multi-variant master plans: parse the variant string in-cell —
  `=IF($R$7="Gro",VALUE(INDEX(SPLIT(G5,"/"),1)),IF($R$7="Res",VALUE(INDEX(SPLIT(G5,"/"),3)),VALUE(INDEX(SPLIT(G5,"/"),2))))`
  Default to the variant matching the project's approved FAR (Oasis FAR 1.8 → the middle/**Vis**
  option), consistent with the variant rule in `apartment-area-uds-statement`. Guard rows with no
  variant string: wrap in `IF(G5="","",…)` so blank rows stay blank instead of `#REF!`.
- **Params must physically sit at the address the formulas reference.** Writing the parameter block
  at the bottom of the sheet while formulas point at `$R$2` gives silently blank/zero results and
  no error — a real trap hit this session. Decide the address first, write params to it, then write rows.
- **Verify by PROPAGATION TEST, not by reading formulas back.** Read the range → change `R2`
  (e.g. 12,000→13,500) → re-read and confirm basic/stamp/reg/GST/total all moved → change it BACK
  and confirm the original values return. Repeat for `R7` (Vis→Gro). Restoring is mandatory: the
  sheet is the user's live document. Then scan the whole data range for `#VALUE!`/`#REF!`/`#N/A`
  (`FORMATTED_VALUE` read, any cell starting `#`) and report "zero formula errors" as evidence.
- Keep the formula architecture when adding a new project tab later (see next section) so all tabs
  in the workbook behave identically.

## Per-unit tab built from a SCANNED area statement — Oasis pattern, 2026-10-13
Ask: "the above area statement is of RANKA OASIS for Upto 130 No. — check sheet Master Area and
find the number of units, take this no of units add to the price sheet and add the other costs to
each unit based on the area mentioned."

1. **Reference-sheet structure to mirror** (the `Master Area` / Master Sheet tab the user points at):
   `Plot # | Length (m) | Breadth (m) | Area (Sqm) | Area (Sft) | Facing | Availability`. Udaya's
   master tab = 38 plots. Oasis has no such tab — its authority is the scanned area statement.
2. **Scanned PDF → tables: render pages with pymupdf, then vision per page.** Text extraction on
   the scan returns only headers; the winning path is
   `pymupdf page.get_pixmap(dpi=200).save(...)` for every page, then `vision_analyze` on each PNG
   in batches of 3–4 (parallel). Prompt: "Extract all text and table data from this page, especially
   plot/villa numbers, areas, and any totals." 10 pages → complete tables, every row's
   plot no / facing / corner / area sft+sqm / FSI options / SBUA options.
3. **The unit count lives in the summary footer of the LAST page — always OCR every page.**
   Oasis page 10 footer reads verbatim: `Corner: 25 | Std: 46 | NS: 40 | Amenity: 4 | Total: 115 plots`,
   alongside the DTCP survey-number list and the six standard notes. Stop after page 9 and you
   never find the count. Reconcile: 25+46+40+4 = 115 = the number of transcribed rows, so
   111 are saleable villa plots and 4 are amenity; the project's approved capacity is "up to 130".
   Report BOTH the drawn count (115) and the approved capacity (130) — they are different things.
4. **Priced rows vs blank rows:** 8 entities (plots 131–138) carry no legible FSI/SBUA on the scan →
   leave their pricing cells blank with a note "pending architect confirmation". Never invent a
   variant to fill the gap. Final tally this build: 115 entities transcribed, 107 priced, 8 pending.
5. **Independent cross-checks to run and report:** corner-labelled rows from the transcription (26)
   vs the statement's own summary (25) — one row to reconcile, flag it rather than silently
   agreeing; total plot area 204,792 sqft (19,026 sqm), avg 1,781 sqft, range 1,093–8,382 sqft;
   total villa SBUA at the Vis option 337,882 sqft → ~₹405 Cr basic at ₹12,000/sqft.
6. **Tab shape** (15 cols): `Plot/Villa No | Facing | Corner | Plot Area sft | Plot Area sqm |
   Villa FSI (Gro/Vis/Res) | Villa SBUA (Gro/Vis/Res) | Villa Area used | Rate ₹/sft | Basic |
   Stamp 7% | Reg 4% | GST 5% | Legal | Total Outflow`, with 3 title/note rows above the header
   and the params block at Q2:R7. Title the tab with the source: "…per unit, from approved Plot &
   Villa Area Statement 18.8.26 — Dwg 04-MP/01 R1".

## Sheets API / Sheets-app gotchas hit on this build (all confirmed by error text)
- **`fontColor` is NOT a field — use `foregroundColor` nested inside `textFormat`**:
  `{"textFormat": {"bold": True, "foregroundColor": {...}}}`. A bare `fontColor` in textFormat →
  HTTP 400 `Cannot find field: fontColor`.
- **The `repeatCell` `fields` mask must be fully qualified.** `"textFormat"` alone → HTTP 400
  `Invalid field: text_format`. Build the mask as `userEnteredFormat.textFormat.bold`,
  `userEnteredFormat.textFormat.fontSize`, `userEnteredFormat.backgroundColor` — i.e. walk the
  nested dict and prefix every leaf with `userEnteredFormat.`.
- **Adding a tab then writing to it**: create via `batchUpdate {addSheet}` first and reuse the
  returned `sheetId` for formatting; guard with a title lookup so a re-run finds the existing tab
  instead of creating duplicates (idempotent build scripts).
- **`=IMAGE()` with Google-hosted URLs renders nothing in Sheets, and the cause is NOT the URL.**
  Drive `uc?export=view`, `lh3.googleusercontent.com/d/<id>=w1000`, API `thumbnailLink` and
  `webContentLink` ALL fail inside Sheets even though curl serves them fine; external hosts
  (catbox/litterbox/telegraph/postimages) were unreachable or rejected, and a neutral Wikipedia
  image URL failed too — including on a brand-new spreadsheet. The definitive error from Sheets is
  **"Please use a desktop web browser to allow access to fetch data from external urls"**: the
  Workspace tenant requires a one-time *Allow external data* grant, and a formula written through
  the API cannot trigger that consent prompt. So: write the logo/`IMAGE()` cell (the DRA logo
  formula is `=IMAGE("https://lh3.googleusercontent.com/d/<logo_file_id>=w1000",1)`), then tell the
  user plainly to open the sheet in Chrome once and click Allow — the row, merge and formula are
  already correct and the image appears on that click. Do NOT keep swapping hosts hunting a URL
  that works; that was ~10 dead calls this session. Fallback if no prompt appears: Insert ▸ Image
  manually, and ask the Workspace admin whether external fetches are blocked outright.
- **Pre-existing logo convention to copy, not invent:** read the existing tab's A1 with
  `valueRenderOption="FORMULA"` and replicate that exact `=IMAGE(...)` string into the new tab
  (Q1 here) so every tab matches.

## Developer-collected cost chain — the FULL buyer outflow (verified 2026-10-13)

The user supplied the standard TN **developer-collected, GST-applicable** component list. These are
NOT in the statutory table above and must appear as their own columns, or the quoted outflow is
understated by roughly 20–25% of the basic price:

| Component | Basis |
|---|---|
| **Basic price** | Villa = land + construction. Quoted either as one ₹/sft on built-up area, or (common in TN villa layouts) as **plot price + construction rate separately**. **Always state which area the ₹/sft sits on** — a rate without a named area is the single most common ambiguity. |
| **PLC / plot premium** | **10% of basic** — corner, road-facing, park-facing, wider-road |
| **Clubhouse / amenity membership** | one-time **₹1–5 L** (villa projects ₹2–5 L typical, sometimes non-refundable) |
| **Infrastructure / development charges** | **₹300 per sft of PLOT** — internal roads, storm drain, STP, street lighting, water treatment, gate |
| **Utility connections** | TANGEDCO EB deposit **₹2 L** + water/sewer **₹1 L** (TN EB deposits run higher) |
| **Legal / documentation / agreement drafting** | **₹1 L** |
| **Patta (TN) transfer** | **₹25,000** |
| **GST** | **5%** on basic + parking + clubhouse + infrastructure |

**The bases are deliberately NOT all "basic price".** GST sits on (Basic + Clubhouse +
Infrastructure); stamp duty and registration sit on (Basic + PLC). A reader who assumes every charge
is a % of basic computes the wrong total, and a chartered accountant will recompute it. Put the base
on the sheet and flag both for Finance to confirm.

### Two header rows: names + basis

Row N = column names, row N+1 = the basis of each charge ("10% of basic", "Rs 300 per sft of PLOT",
"on Basic + PLC", "one-time, non-refundable"). This makes the sheet quotable to a customer without
them opening the parameter block, and it stops the header drifting away from the parameter.

### Column layout when the full chain is added (Ranka Oasis, 2026-10-13)

The 15-column shape above grows to **21 columns A–U**:

```
A Plot/Villa No   B Facing   C Corner   D Plot Area sft   E Plot Area sqm
F Villa FSI (Gro/Vis/Res)   G Villa SBUA (Gro/Vis/Res)   H Villa SBUA used
I Rate Rs/sft (on SBUA)     J Basic Cost
K PLC / Plot Premium        L Clubhouse / Amenity        M Infrastructure / Dev Charges
N Utility Connections       O Legal / Documentation      P Patta Transfer
Q GST                       R Stamp Duty                 S Registration
T TOTAL OUTFLOW             U PLC Override %   <- helper, keep LAST
```

**The parameter block must MOVE when the data widens.** It lived at `Q2:R7`; with data now running
to column U it moved to **`V1:W13`** and every absolute ref changed with it — `$W$2` rate,
`$W$3` SBUA selector, `$W$4` PLC %, `$W$5` clubhouse, `$W$6` infra ₹/sft, `$W$7` EB, `$W$8` water,
`$W$9` legal, `$W$10` patta, `$W$11` GST, `$W$12` stamp, `$W$13` registration. Move the block in the
same pass as the widening and re-point every formula (see the params-address trap above).

### PLC auto-detect + per-row override

Corner status is already a column, so derive the premium rather than asking:

```
=IF($U6<>"",ROUND($J6*$U6,0),
 IF(ISNUMBER(SEARCH("Corner",$C6)),ROUND($J6*$W$4,0),0))
```

`SEARCH` (not `FIND`) so case never matters, wrapped in `ISNUMBER` because it errors on no-match.
Column **U is the escape hatch** for premiums the source data cannot tell you — road-facing,
park-facing, wider-road. The user types a % in that row and it wins.

### GST off a composed base, and TOTAL as a SUM

`=ROUND(($J6+$L6+$M6)*$W$11,0)` for GST (Basic + Clubhouse + Infrastructure), and
`=SUM(J6:S6)` for the total. The plain SUM makes the verification invariant checkable in one pass:
every priced row must satisfy `TOTAL == sum(J..S)` — report the count of failures, expect zero.

### Payment-schedule tabs reference the price list by CELL

`='Oasis - All Units (Area Stmt)'!J11` for basic, `!T11` for total, and pull the row label
dynamically too (`="Plot "&'Oasis - All Units (Area Stmt)'!A11`) so the schedule stays
self-describing if the user repoints it. **When the price-list tab is restructured, re-point every
cross-tab formula in the same pass.**

## WORKBOOK-WIDE error sweep — after ANY structural change (the 2026-10-13 defect)

**Renaming or replacing a tab silently breaks formulas in every OTHER tab.** A `Payment Schedule`
tab pointed at `'Oasis - Villa Price List'!F3`; that tab had been renamed to
`Oasis - All Units (Area Stmt)`, so three rows had been returning `#REF!` and nobody noticed — the
renamed tab itself looked perfect. **The tabs you did NOT touch are the ones most likely to be
broken.**

- Sweep **every tab**, not just the one you edited: read each with
  `valueRenderOption="UNFORMATTED_VALUE"` and flag any cell whose string starts `#` (`#REF!`,
  `#VALUE!`, `#N/A`, `#DIV/0!`, `#NAME?`, `#ERROR!`, `#NULL!`, `#NUM!`).
- Re-runnable probe: **`scripts/sheets_error_sweep.py`** in this skill — takes a spreadsheet id,
  lists every tab with row/populated counts and error cells, exits non-zero if any error is found,
  so it can gate a build pipeline.
- Report "zero error cells across all N tabs" as evidence, and name any tab you had to repair.

## Preserve user-edited parameter cells — flag, never silently overwrite

A rebuild found the rate cell at **9999** (a placeholder) and registration at **2%** when the TN
standard is 4% — while the old column header still read "Registration 4%", i.e. the header and the
parameter had drifted apart. Both cells had been changed by the user, not by the build. The correct
move is to **carry the current value forward and flag it in the reply**: silently "correcting" a
price or a statutory rate is the worst possible outcome of a rebuild. Corollary: don't hardcode a
rate into a column header, or it will drift from the parameter that actually drives the maths.

## Agency mismatch between a supplied cost spec and the project's location

A cost spec supplied **CMWSSB** (Chennai Metro Water) as the water/sewer authority for Ranka Oasis,
which is in the **Hosur** belt — the correct body there is the local municipality / TWAD. Keep the
amount, label the line generically ("Water & Sewer Deposit"), and flag the mismatch rather than
quoting a Chennai agency to a Hosur buyer.

## Area-variant default is a pricing decision, not a detail

The SBUA selector must be set to the variant matching the project's **approved FAR**
(Oasis FAR 1.8 → the **Vis**/Vista option — see `apartment-area-uds-statement`). A build defaulting
to the largest variant silently overprices every row. State which variant is live and flag it. (The
2026-10-13 Oasis tab was left on `Gro`, which is NOT the approved-FAR variant — check before the
sheet is quoted from.)

