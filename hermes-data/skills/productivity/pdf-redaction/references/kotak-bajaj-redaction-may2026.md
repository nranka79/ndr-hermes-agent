# Kotak Bank Statement — Bajaj Insurance Redaction (May 2026)

## Source file
`/data/hermes/document_cache/doc_f85bc2e53624_NDR_Kotak_Bank_Sst_Bajaj_insurance_payment_and_receipt_details_2.pdf`
8 pages, Kotak Bank statement, NDR (likely Nostro/Domestic Rupee) account.

## Verified keep zones

### Page 3 — Bajaj Debit (CONFIRMED ✅)
- **Entry**: Debit ₹73,066 to BAJAJ. Reference: `KKBKH25072718391/BAJAJ`
- **Page layout**: Page 3 is the FIRST page with transactions (after title page + page 2 header only)
- **Printed row y-range**: y=1480 to y=1525
- **Handwritten annotation y-range**: y=1550 to y=1573
- **Keep zone**: **y=1480 to y=1575** (with margin to capture both printed row + handwriting)
- **Verification**: Crop at y=1480-1575 shows the full debit entry with handwritten "My Sent" + "to Bajaj Allianz" lines

### Page 8 — Bajaj Credit (UNVERIFIED — needs user confirmation)
- **Entry**: Credit ₹73,066 from BAJAJ ALLIANZ LIFE INSURANCE. Reference: `NDR/250527004771`
- **Suspected keep zone**: y=790 to y=890
- **Issue**: Multiple vision attempts misidentified which page contained the credit entry; page numbering got confused with page 3
- **What to do**: Open `/tmp/kotak_final3/p8.jpg` and visually confirm the credit row at y=790-890. If blank/wrong, scan pages 4-8 with pixel density scans to find where the BAJAJ ALLIANZ credit row actually sits.

## Output files from this session
- `/tmp/kotak_final3/p3.jpg` — rendered page 3
- `/tmp/kotak_final3/p8.jpg` — rendered page 8
- `/tmp/kotak_final3/p3_v1_zone.jpg` — crop showing page 3 Bajaj debit (verified)
- `/tmp/kotak_final3/v3_redacted_p3.jpg` — attempt 3 redaction of page 3
- `/tmp/kotak_final3/v3_redacted_p8.jpg` — attempt 3 redaction of page 8

## Root cause of redaction failures
Vision was calling the wrong page numbers. The statement has 8 pages but the debit is on page 3 (not page 7 as first identified from filename). The credit is on page 8 (not page 5). Always pixel-density scan pages rather than assuming filename order.

## Workflow to follow
1. Render all pages: `pdf2image.convert_from_path(input, dpi=150)`
2. Pixel-density scan: find pages where pixel count at expected row y is high (target rows are dense with text — black pixels dominate)
3. Save crop of suspect zone, verify with vision
4. Apply keep zones to build black-overlay image
5. Composite and save as flattened JPEG → embed in pymupdf