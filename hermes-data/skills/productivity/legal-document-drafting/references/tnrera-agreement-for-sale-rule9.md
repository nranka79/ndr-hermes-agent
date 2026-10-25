# Plot allotment: Agreement for Sale (TNRERA Annexure 'A', Rule 9 model)

When Bharat/NDR asks for an **Agreement of Sale / Agreement for Sale / Agreement to Sell**
for a Ranka Udaya (or any DRA plotted-layout) plot — especially "change this To Agreement
of sale" or "he has paid the full money, mention full amount received" — the deliverable is
NOT a re-titled absolute sale deed. Use the **TNRERA Annexure 'A' model form** (Rule 9,
"Agreement for Sale", the PDF Bharat keeps sending) with the Promoter/Allottee structure.

Verified 12-Oct-2026: DRAFT for **Plot 31 → Rajani Jaisimha Rao** built from the Plot 36
absolute-sale-deed Google Doc (parties/title chain/approvals) + the TNRERA model PDF
(clause structure). Uploaded as native Google Doc + raw .docx to Ranka Udaya Title folder.

## Which document is which (do not mix them up)

- **Absolute Sale Deed** (existing drafts: Plot 34→Manohar, Plot 36→S Ravi Kumar):
  VENDOR/VENDEE; "hereby SELLS, TRANSFERS, CONVEYS"; transfer-of-title + TDS 194-IA clauses;
  use `references/plotted-layout-sale-deed-update.md` for the new-buyer/new-plot flow.
- **Agreement for Sale** (this reference): PROMOTER/ALLOTTEE; covenant to transfer when the
  future Sale Deed is registered; used when allottee has paid (fully or in part) but the
  deed is not yet registered.

## Sources to combine (in order)

1. **Existing absolute sale deed in the same layout** (Google Doc in Ranka Udaya Title,
   id `1SxLbgAHXqwETKKceYmHjAn4mZ6pyoJdD`) — reuse VERBATIM: Promoter party block (DRA
   Thindlu Land Partners via partners DRPL/Kishan Murjani Nair + Nishant Ranka), full title
   chain (Gift 10658/2022 → Rectification 11162/2022 → Partition 11721/2024 → Sale Deed
   20527/2024), HNTDA approvals SWP 90/2025+38/2025, DTCP Layout 90/2025,
   Panchayat ROC 02/2025-2026, RERA **TNRERA/30/LO/0642/2026** dt 18.02.2026
   (File TNRERA/PLI/9954/2025), gift deeds 1634/2025 (TANGEDCO) + 1632/2025 (Panchayat).
2. **TNRERA Annexure 'A' model PDF** (Rule 9) — the operative-clause skeleton:
   recitals A–I, clauses 1–25, Schedules A/B/C, execution blocks.
3. **Master sheet** — `Ranka_Udaya_Master_and_Cost_Sheet (1)` id
   `1mtqU51isImvtEmqEIuuqNmeeycV5zMxhjT7tXNiaao8`, tab Master Sheet: plot dims/area/facing.
4. **Purchaser identity from scanned PAN + Aadhaar** (PDFs sent by user) — see OCR notes.

## Structure of the Agreement for Sale

- Title block: `ANNEXURE 'A'` / `AGREEMENT FOR SALE` / `[See Rule 9 ... Rules, 2017]` /
  `RANKA UDAYA — RESIDENTIAL PLOT LAYOUT ...` / `PLOT NO. N`
- Parties: PROMOTER (firm + partners, as in sale deed) ... AND ... ALLOTTEE
  (Ms./Mr. FULL NAME, S/o/W/o/D/o, age, DOB, PAN, Aadhaar, address). Use "aged about X
  years" — compute from DOB at signing date, beware the birthday boundary (born 24/10/1970
  → still **55** on 12-Oct-2026, turns 56 on 24-Oct).
- Recitals A–I (plotted-development variant B/C: layout approval + RERA + gift deeds).
- Clauses 1–25 of the model, adapted to plotted development:
  - Clause 1: consideration, payable per Schedule C.
  - Clause 2: no subsisting charge/encumbrance.
  - **Clause 3 — FULL AND FINAL PAYMENT** (the key clause when money already received):
    "entire Consideration of Rs.____ (Rupees ____ Only), being 100% of the total sale
    consideration, has been paid to and received by the Promoter prior to execution;
    Promoter acknowledges receipt in full and confirms no amount remains due; Promoter
    shall execute/register the Sale Deed within 90 (ninety) days of the Allottee's
    request, or as mutually agreed."
  - Drop/repurpose the model's apartment-specific clauses (construction agreement,
    loan disbursement to promoter) — plotted variant goes straight to assignment fee,
    registration of future deed on receipt of all monies, default/cancellation.
  - Clause covering default still applies for non-payment duties (cancellation + refund
    per Act/Rules) even when full payment made.
  - TDS 194-IA clause: include only if consideration < ₹50L (kept as in DRA practice).
  - Disputes: amicable → RERA adjudicating officer; courts at Krishnagiri.
- Schedules: **A** = whole layout land (Sy 240/3A, Hec 0.70.76/Ac 1.75, boundaries per
  title: E Sy 240/4A,240/1C,240/4B / W Sy 240/2 / N Panchayat Road / S Ac 0.08 Sy 240/3);
  **B** = plot (no., area sqm + sft, dims E-W then N-S, facing, boundaries, neighbours);
  **C** = payment schedule → when fully paid, state "entire consideration paid & received
  in full"; leave cheque/DD/UTR particulars blank for execution day.
- Execution: Promoter (both partners) / Allottee / 2 witnesses / PLACE Bagalur / DATE blank.

## Boundaries for a newcomer plot (same derivation as sale deeds)

Plots 1–19 face West, 20–38 face East, serpentine numbering; road on facing side
(East = 9M internal road), layout boundary at rear (West = Sy 240/2A2); neighbours are
N−1/N+1 in-row, higher number = North. Verify on approved drawing, put in "confirm before
registration" list, never silently copy.

## Consideration

Use the **user-stated total** (e.g. ₹33,00,000) even if it differs from master-sheet
rate × area (₹3,500/sft → Plot 31 ≈ ₹42.57L). Do NOT silently re-price. Show the rate
difference in the confirm list ("₹33L ≈ ₹2,713/sft vs standard ₹3,500/sft — confirm").

## OCR of scanned PAN/Aadhaar for party blocks

- `pdftotext` returns NOTHING for scanned cards → render pages with pymupdf
  (`page.get_pixmap(dpi=300-350, colorspace=pymupdf.csGRAY)`), then OCR the PNG.
- vision_analyze refuses PDFs (`Only real image files are supported`) — render to PNG first.
- **Aadhaar PDFs often render rotated 90°** — tesseract gives pure garbage on a rotated
  page; rotate 180 / ±90 / mirror and re-OCR until readable (this session: 90° CCW won).
- Aadhaar number may print reversed/masked; check both front and back faces. The back
  face carries "Your Aadhaar No." — full 12 digits often only there
  (e.g. 5071 2010 7875). Front may read slightly different name ("Rajan" vs "Rajani").
- PAN is authoritative for: exact name (uppercase), father's name, exact DOB
  (24/10/1970), PAN no. Aadhaar gives DOB year, gender, address.
- If PAN father ≠ Aadhaar S/o-W/o relation (e.g. PAN father "Tumukuru Seetharamaiah
  Raghavendra Rao" vs Aadhaar "W/o Jaisimha Rao"), print the Aadhaar relation in the
  party block and flag the mismatch in the confirm list — never guess.
- Address on Aadhaar front may need contrast enhancement (autocontrast + upscale) for
  the unit number ("A2-500" vs "A2-603") — still flag it.

## Deliverable + verification

- Filename: `YYYYMMDD RankaUdaya_AgreementForSale_PlotNN_<AllotteeName>` (native Google
  Doc) + `.docx` (raw), both into Ranka Udaya Title folder.
- Verify the CONVERTED Google Doc (not just the .docx): pull via Docs API and check key
  strings (amount, PAN, Aadhaar, plot no., area) survived conversion.
- Reply shape: Drive links first, then change list, then numbered "confirm before
  registration" list (consideration basis, father/spouse relation, boundaries, payment
  particulars, execution date).