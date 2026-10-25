# Plot-layout Agreement for Sale (TNRERA Annexure 'A' model) — new buyer / full payment

Companion to `plotted-layout-sale-deed-update.md`. Use that reference for the Absolute Sale Deed
re-issue workflow; use THIS one when Bharat/NDR says some mix of:

- "change this to Agreement of Sale / Agreement to Sell" (converting the Absolute Sale Deed template)
- "he has made the payment of X lakhs already, mention full money has been received by promoter/developer"
- "create a separate word doc taking the reference I shared" + buyer PAN/Aadhaar PDFs attached

Verified 12-Oct-2026: Plot 36 Absolute Sale Deed reference → Plot 31 Agreement for Sale,
buyer Rajani Jaisimha Rao, ₹33,00,000 fully paid.

## The legal form to use

Use the **TNRERA model "Agreement for Sale" (Annexure 'A', Rule 9 of the TN RERA Rules 2017)** —
not a converted sale-deed structure. Bharat supplies the model PDF; the canonical structure is:

1. **Parties**: PROMOTER (M/s DRA THINDLU LAND PARTNERS party block, same as sale deed) +
   ALLOTTEE (buyer — the model says "Allottee", not "Vendee")
2. **Recitals A–I** (ownership/title chain; plotted-development scheme; layout sanctions;
   RERA registration; gift deeds for roads; allottee verification; offer to purchase the plot;
   promoter competence; reduction to writing)
3. **Operative clauses 1–25** of the model, adapted:
   - omit apartment/construction-specific clauses (loan disbursement, construction agreement,
     joint-allottee clauses) for a plotted layout
   - clause 1 states the consideration; insert the FULL-PAYMENT clause (below)
   - registration clause: since entire consideration already received, Promoter shall execute
     and register the Sale Deed within 90 days of the Allottee's request (or as agreed)
   - keep dispute resolution via RERA adjudicating officer + courts at Krishnagiri
   - keep a Sec 194-IA TDS clause (below ₹50L → not applicable; re-check on large plots)
4. **Schedules**: A = total land (Sy 240/3A, Sevaganapalli, extents, boundaries from title
   chain); B = plot (number, area sqm+sqft, dimensions, boundaries, facing); C = payment
   schedule (turned into "full amount paid and received" when money already collected)
5. Execution blocks for Promoter (both partners), Allottee, witnesses; place Bagalur.

## FULL-PAYMENT clause pattern (the key user ask)

When the buyer has already paid 100%, add a dedicated clause (e.g. Clause 3) worded:

> "FULL AND FINAL PAYMENT — The Allottee has already paid to the Promoter, and the Promoter has
> received, the entire Consideration of Rs.___ (Rupees ___ Only), being 100% of the total sale
> consideration, prior to the execution of this Agreement. The Promoter hereby unequivocally
> acknowledges receipt of the full and final Consideration ... and confirms that no amount
> whatsoever remains due or payable by the Allottee ... The Promoter shall ... execute, sign and
> register the Sale Deed ... within 90 (ninety) days from the date of such request."

Schedule C should repeat the receipt declaration and leave cheque/DD/UTR particulars blank
("payment particulars to be furnished at the time of execution") — never invent bank details.

## Consideration arithmetic — flag, don't silently adjust

- Master sheet rate is ₹3,500/sft (Plot 31 = 1,216.28 sft → ₹42.57L), but the dictated agreement
  amount may be lower (₹33L ≈ ₹2,713/sft here). Bharat's stated figure IS the deal — use it as the
  Consideration, and flag the per-sqft difference on the "confirm before registration" list.
- Legal & Handling ₹20,000 is NOT folded into the agreement consideration — mention separately if needed.

## Buyer identity from scanned PAN/Aadhaar

PAN/Aadhaar arrive as scanned PDFs (pdftotext returns empty). Pipeline:
1. `pymupdf` render each page at **dpi=350 grayscale** (`get_pixmap(dpi=350, colorspace=pymupdf.csGRAY)`)
2. Aadhaar letter pages are often **rotated/mirrored** — try `rotate(-90, expand=True)` (CCW) before OCR;
   the "Government of India" back-face carries DOB/year-of-birth + gender + the full Aadhaar number
   (front face shows masked/partial number). See ocr-and-documents `references/aadhaar-pan-card-extraction.md`.
3. Crop regions (name/father block, number block, address block), autocontrast, 3-4x resize, tesseract `--psm 6`.
4. **Cross-check PAN vs Aadhaar**: name, father name, DOB format, gender, relation (S/o vs W/o) can
   disagree — put EVERY discrepancy on the confirm list; use PAN for name/DOB when they conflict.

## Verification + delivery (same as sale-deed workflow)

- python-docx (A4, Times New Roman 12, justified); check every key figure + name case-insensitively
  before upload (the classic failure is a half-updated amount in TDS or market-value clause).
- Upload BOTH a converted native Google Doc AND the raw .docx into the project Title folder
  (Ranka Udaya Title = `1SxLbgAHXqwETKKceYmHjAn4mZ6pyoJdD`); verify the converted Doc via Docs API
  text read-back, not just the .docx.
- Reply shape: Drive link first, then bullet list of every change, then a short numbered
  "confirm before registration" list (consideration basis, father/husband name, plot boundaries,
  payment particulars, execution date).