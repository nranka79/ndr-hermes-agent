# Ranka Oasis — Sy 176 & 177 Title Extent Verification (2026-09-22)

The user's recurring diligence question: "lands received in survey 176/177 — what total extent did we purchase by sale deed and by exchange deed?" Verified turnkey from the actual registered deeds (not the master-data workbook). This reference is the canonical answer + the reading workflow.

## The answer: 64 cents total (0.64 acres) in Sy 176/177

### Via Exchange Deed — 50 cents (the primary acquisition)
- **Deed:** Doc. 4292/2024, Book I, SRO Hosur, dated 16-Feb-2024
- **Parties:** DRA Realty Pvt Ltd (First Party) ↔ **Venkatamma** (Second Party; W/o late Kencha Reddy's estate; SPA holder Rajendra S V)
- **What DRA received (Schedule B):**
  - Sy 177/1A (new Sy 177/1A1) — **23½ cents** (Dry, out of Hec 0-16.00)
  - Sy 176/1B (new Sy 176/1B2) — **3½ cents** (out of Hec 0-46.50)
  - Sy 176/2 (new Sy 176/2B) — **23 cents** (out of Hec 0-75.00)
  - **Total = 50 cents**, value Rs 2,56,50,000. South boundary = 18+ m frontage on Chichuraganapalli–Sevaganapalli Road.
- **What DRA gave (Schedule A):** Sy 14/7 (new 14/7B) 23 cents + Sy 14/2 full 72 cents = **95 cents**, value Rs 1,15,00,000. Stated purpose: secure clear 12+ m road access from the Chichuraganapalli–Sevaganapalli Road to the SE corner of Sy 166/2B.
- Drive copies: `20240216 Exchange deed 4292 for Syno-177-1A,176-2B,176-1B2.pdf` — e.g. `https://drive.google.com/file/d/1tpqk_HWICBlwQi-y2cNr5Q13HRWTAQhP/view` (also in "Registered sale deeds sevaganapalli" folder `19t4HNYKoqrS3yxz6WSNNmU3cOQhGF3a5`).

### Via Sale Deed — 14 cents (additional 177 land)
- **Deed:** Ramappa & family (heirs of Venkataramanappa / Butta Reddy line) → **Sevaganapalli Land Partners**, executed 1-Mar-2024 at Hosur (Drive Google Doc `PS SALE DEED SEVAGANAPALLI SY. NO. 177-4A2 177-5A2 RAMAPPA TO SEVAGANAPALLI PARTNERS-1` — `https://docs.google.com/document/d/14zDUCXpV9Nv_4UvH6_V2uENKnsIWiKxGI0EFnT3qqFg/edit`)
- Sy 177/4A2 — 5¾c; Sy 177/5A2 — 2¼c; Sy 177/4A1 — 3c; Sy 177/5A1 — 3c. Total **14 cents**, value Rs 2,05,00,000. Boundaries: N = Sy 177/1A & 177/1B, S = Chichuruganapalli Panchayath Road. Source: partition deed 3076/2001 (12.09.2001).
- This Google Doc may be a final/unsigned copy — if the user needs the REGISTERED copy with document number, locate at SRO or ask.

### The 7.53-acre "main" sale deed does NOT include 176/177
- Doc. **21201/2023** of 2023 Book I, SRO Hosur, 16-Oct-2023, vendee **M/s Sevaganapalli Land Partners** (Nishant Ranka + Srinivas Krishnappa), 116 vendors (incl. GPA holders Pavan Kumar; the "7.53 acres" copy is `20231016 sale deed (7.53 acres).pdf`, 60 MB, ~148 PDF pages).
- Schedule items 1–19 (sheets ~54–55) cover ONLY: 158/1A1, 158/1C2, 158/1C3, 158/1C9B, 166/3A, 166/3B, 166/3C, 166/3D, 166/3E1, 166/3E2, 166/3F, 167/1A, 167/1B, 167/1D, 167/1H, 167/1I, 167/2D = 7.53 ac total, value Rs 4,46,60,000. **Sy 176/177 never appear** — do not assume the Oasis bulk purchase carries them; all 176/177 title came via the two deeds above.

### Title chain for the exchange portion (from deed 4292 recitals)
Kencha Reddy bought 176/1 (1.25 ac), 176/2 (1.85 ac), 177/1A (0.40 ac) from Clover Estate Pvt Ltd (sale 4879/2004, 26-08-2004; Clover's own source: Muraligopal via GPA Nandhagopal, sale 3428/2004) → 2005 exchange 4767 with Clover (0.32c 176/2A moved in, 0.09c 176/1B / 0.08c 176/2B / 0.14c 177/1A moved out) → Kencha Reddy died 17-01-2016; heirs: Venkatamma + sons Venkatesh Reddy, Narayana Reddy + daughter Lakshmamma → partition 1611/2024 (30-Jan-2024) allotted the A-schedule to Venkatamma → **exchange 4292/2024** to DRA. Related: `20240302 DRA Venkatappa 176-1B/176-2B/177-1A RTGS consideration` Google Doc confirms the payment leg.

## Scanned registered-deed reading workflow (no text layer)

`pdftotext` returns 0 lines on these OKEN-scanned deed PDFs. Pipeline that worked:
1. `fitz.open()` (pymupdf) → count pages → render 150 DPI PNGs (`page.get_pixmap(dpi=150)`).
2. `vision_analyze` per page with specific prompts. Page map for a 25-page exchange deed:
   - p1: parties + date + doc no.
   - p3–7: recitals = full title chain (lineage, deceased heirs, prior deeds with doc numbers).
   - p8–9: operative clause (who conveys what to whom — Schedule A to Second Party, Schedule B to First Party).
   - p10: **Schedule A** (what DRA gives) — starts "DESCRIPTION OF THE PROPERTY / SCHEDULE - A".
   - p11: **Schedule B** (what DRA receives) — same header; note it "out of this an extent of Acre X" phrasing → the NEW sub-division number is the current holding.
   - Later pages: signatures, then Aadhaar copies — NOT schedules.
3. **Landscape pages** render sideways → `matrix=fitz.Matrix(150/72,150/72).prerotate(90)` (test 90 vs 270; the schedule pages were portrait after all, Aadhaar pages landscape).
4. **Registration stamp offset**: "Contains N Sheets — K Sheet" maps sheet→PDF page with an offset (e.g. sheet 54 ≈ PDF p59 because earlier pages are annexures). For the 142-sheet 21201/2023 deed, the vendor list + signatures fill sheets 1–~40; the **property schedule sits at sheet ~54–55 (the middle/end of the printed text), NOT at the very end of the PDF** (end pages = life certificates + deficit-fee certificate).
5. Always identify **which Schedule is which**: buyer = First Party receives Schedule B in a "First Party shall convey Schedule A ... in lieu thereof the property in Schedule B to the First Party" deed, but check each deed's operative clause — it varies by who drafted it. Extract the exact acreage sentence ("Altogether making total an extent of Acre X") and the boundary block.