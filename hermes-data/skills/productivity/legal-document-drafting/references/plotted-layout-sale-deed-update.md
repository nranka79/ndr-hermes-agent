# Updating a plotted-layout sale deed draft for a new plot / new buyer

> **Sibling workflow:** if the ask is an **AGREEMENT FOR SALE / Agreement to Sell**
> (not an absolute sale deed) — e.g. "change this To Agreement of sale", "full money
> received, mention it" — use **references/tnrera-agreement-for-sale-rule9.md**
> (TNRERA Annexure 'A' Rule 9 model, Promoter/Allottee structure, FULL-AND-FINAL-PAYMENT
# Updating a plotted-layout sale deed draft for a new plot / new buyer

> **Agreement for Sale (not the deed)?** When the ask is to convert the deed into an
> **Agreement for Sale / Agreement to Sell** (e.g. buyer has already paid in full) use
> `references/plotted-layout-agreement-for-sale.md` — it covers the TNRERA Annexure 'A'
> model, the FULL-PAYMENT clause pattern, and buyer-identity extraction from PAN/Aadhaar scans.

The DRA Ranka Udaya pattern (verified 25-Sep-2026: draft for **Plot 34 → Manohar Manohar Singh**
re-issued as **Plot 36 → S Ravi Kumar**). Also applies to any DRA plotted layout
(Ranka Udaya / Saveganapalli, Ranka Oasis, etc.) and to apartment deeds.

## Trigger

Bharat/NDR hands over an existing executed-style **.docx draft** and says some mix of:

- "this is the draft, only replace <old buyer> and his details with the new details"
- "update the dates and all for today"
- "we have sold it at Rs.X per square foot for plot number NN"
- "the plot details you will get in the master sheet"
- "whatever you have updated, show me in highlighted, that is yellow in colour"
- "give me the drive link for the same"

## Cadence

1. **Inventory before editing.** Read the whole .docx and list every party-specific datum that
   has to move. Miss one and it ships wrong:
   - vendee party block (name, S/o, age, DOB, PAN, Aadhaar, address)
   - operative clause plot reference ("ALL THAT piece and parcel … being Plot No. N")
   - Schedule of Plot: number (figures **and** words), total area (sqm + sqft), the four
     dimensions, the four boundaries
   - the consideration figure — it appears ~8 times, each with **figures AND words**
     (recitals, operative clause, TDS clause, consideration clause i/ii/iii, market-value
     declaration, payment-mode clause)
   - payment-mode clause (cheque/DD no., date, bank)
   - signature blocks in the body **and** the page footer
   - Annexure A plot reference
   - both date sites: the opening "ON THIS THE … DAY OF …" and the foot "DATE:" strip
2. **Pull the plot's authoritative data** from the project master sheet — never carry it over
   from the old deed or from memory.
3. **Rebuild the .docx** with the changed spans highlighted yellow — `scripts/docx_yellow_diff.py`.
4. **Verify** (all three, not just one): 0 stale references left; highlighted run count > 0;
   render at least one page and eyeball the yellow band.
5. **Upload**: a converted Google Doc (so the highlight is visible and the link stays stable)
   plus the raw .docx alongside it, into the project's Title / sale-deed folder; hand back the link.

## Ranka Udaya data sources

- **Master sheet** — `Ranka _Udaya _Master_and_Cost_Sheet (1)`, id
  `1mtqU51isImvtEmqEIuuqNmeeycV5zMxhjT7tXNiaao8`. Tab *Master Sheet* rows 4–41:
  `Plot # | Length (m) | Breadth (m) | Area (Sqm) | Area (Sft) | Facing | Availability`.
  Tab *Cost Sheet*: plot no entered in **C5**; Facing/dims/area come in by VLOOKUP;
  `Plot Cost = Area (Sft) × Rate per Sft (C6)`; `Grand Total = Plot Cost + Legal & Handling (C7,
  default Rs.20,000)`.
- **Approved layout / area cross-check** — `20260911 Ranka Udaya Unit Nomenclature – Phase I`,
  id `1FqLNX8LL8ATc3dWcsFGQEBycN_EGZIJRdcC9jekav00` (tabs: Nomenclature, Physical Area Statement,
  Approved Layout Plan, Plotwise Comparison). *Plotwise Comparison* flags dims-vs-stated-area
  mismatches — plot 1 is −7.37%, most others ≤1%.
- **Source draft folder** — `Ranka Udaya Title`, id `1SxLbgAHXqwETKKceYmHjAn4mZ6pyoJdD`.
- Vendor = **M/s DRA THINDLU LAND PARTNERS** (PAN AAXFD2296G); registration at Sub-Registrar
  **Bagalur**, Krishnagiri District, TN; project RERA **TNRERA/30/LO/0642/2026** dt 18.02.2026.
- Plot 36 reference values: 9.16 m × 12.19 m, 111.864 sqm / 1,204.09 sqft, East-facing.

## Consideration arithmetic

Deed consideration = **plot cost only** (area × rate), matching the pattern of the prior deeds
in the same layout. Do **not** silently fold in the Cost Sheet's Legal & Handling charge — state
the grand total separately in the reply and let the user choose. At Rs.3,500/sft the
Rs.50,00,000 Sec 194-IA TDS threshold is crossed above ~1,428 sqft, so re-check the "no TDS"
clause on every far-larger plot instead of copying it.

## Boundaries — derive, then flag. Never guess, never silently copy

- The Ranka Udaya master plan (`Ranka Udaya Master Plan (2).pdf` on Drive) carries **no north
  arrow**, and neither do the North Star sanction sheets. Orientation has to be reconstructed.
- Reconstruction that works: combine the master sheet's **Facing** column with the drawing.
  Ranka Udaya = two rows of plots separated by a **9 m** central internal road, a **10 m**
  vertical road splitting the middle, approach road (Chichuraganapalli Road) at one short end.
  Schedule A of the parent land fixes the compass: **North** = Panchayat Road, **West** = Sy 240/2,
  **East** = Sy 240/4A / 240/1C / 240/4B, **South** = Ac.0.08 cts in Sy 240/3 (C.R. Vinodha).
  Plots **1–19 face West**, **20–38 face East**, numbered in a **serpentine** (1 at one short end
  of one row → 19 at the other end → 20 back along the far row → 38 at the far end). So a plot's
  neighbours are **N−1 and N+1 within the same row**, the road is on its facing side, and the
  layout boundary is at its rear.
- **The inherited boundary block is not trustworthy.** The plot-34 draft gave `West: Road` for a
  plot the master sheet records as **East-facing**, and neighbours `North: Plot 33 / South: Plot
  32` when plot 34 sits between 33 and 35. It was internally inconsistent on both axes.
  Derive the four boundaries, put them in, and put them on the "confirm before registration"
  list in your reply.

## Pitfalls

- **python-docx `doc.paragraphs` does not include paragraphs inside tables.** Signature/execution
  blocks and page footers are almost always tables. Iterate
  `doc.element.body.iter(qn('w:p'))` (and each `section.footer._element.iter(qn('w:p'))`) and wrap
  in `Paragraph(el, doc)`, or the outgoing vendee's name survives in the footer of every page.
- **`<w:highlight w:val="yellow"/>` must sit in OOXML rPr schema order** — after `w:sz`/`w:szCs`
  but *before* `w:rtl`. Blindly appending it to the end of rPr can render nothing. In .docx always
  use `w:highlight`, **never `w:shd`** — `w:shd` is frequently invisible in Google Docs.
  `scripts/docx_yellow_diff.py` does the ordered insert for you.
- **Verify the yellow survived the Google-Docs conversion** by counting runs with
  `textStyle.highlightColor` via `docs.documents().get()` on the converted Doc. A w:highlight
  present in the .docx is not proof the rendered Doc shows it.
- **Do not re-pitch edits against the old numbers.** Restate each changed value in figures *and*
  words at every occurrence — a half-updated amount in the TDS or market-value clause is the
  classic failure.
- **/tmp filename collisions**: a leftover root-owned file (e.g. `/tmp/verify.py`) makes a heredoc
  write fail with "Permission denied". Pick a new filename; don't fight it.

## Agreement of Sale variant (not Absolute Sale Deed)

If the user asks to turn the deed into an AGREEMENT FOR SALE (TNRERA Annexure 'A' / Rule 9
model — e.g. buyer has already paid the full amount and registration is deferred), see
`references/tnrera-agreement-for-sale.md`. Different clause order, Promoter/Allottee
parties, dedicated full-payment-received clause, Schedule C = payment schedule. Same master
sheet / title-chain / KYC-extraction data sources as this reference.

## Reply shape

Drive link first, then a bullet list of every change, then a short numbered
**"confirm before registration"** list (boundaries, payment particulars, consideration basis).
Bharat is cost/token conscious — keep exploratory forensics (drawing reverse-engineering, page
tiling) short, and say when a step is getting expensive rather than grinding silently.
