# ATS vs Sale Deed Cross-Check — Embassy Habitat 914 (June 2026)

## Document Pair Identified
- **ATS** (Agreement to Sell): Registered Doc No. GNR-06465-2025-2026, 05.03.2026, Gandhinagar SRO
  - File ID: `1NHTjby2nWSCJk86_L4UXt96A75nCiiI0` (PDF)
- **Sale Deed**: Google Doc ID `1yHiL4vSGjhyEPOfX3g_Q_LiUsRZWlG61_BROKCUkIL8` → exported as PDF

## Key Figures (Verified Matched)

### Parties
| Field | ATS (05.03.2026) | Sale Deed (05.04.2027) |
|-------|-----------------|------------------------|
| Seller | Ravikumar Kubasing Naik | Ravikumar Kubasing Naik |
| Father's Name | Kubasing Hemlappa Naik | Kubasing Hemlappa Naik |
| Seller Age | ~57 years | ~58 years |
| Seller Address | H.No.01, 3rd B Cross, Gururaja Layout, Doddanekkundi – 560037 | Same |
| Seller PAN | ABWPN6886E | ABWPN6886E |
| Seller Aadhaar | 7541 2533 7406 | 7541 2533 7406 |
| Purchaser | Roshini Ranka | Roshini Ranka |
| Purchaser's Husband | Nishant Ranka | Nishant Ranka |
| Purchaser PAN | AJWPR4496E | AJWPR4496E |
| Purchaser Aadhaar | 2695 5572 3535 | 2695 5572 3535 |

### Property Details
| Field | ATS | Sale Deed |
|-------|-----|-----------|
| Flat No. | 914 | 914 |
| Floor | First Floor | First Floor |
| Wing | Ninth Wing | Ninth Wing |
| Block | Second Block | Second Block |
| Address | 59, Palace Road, Vasanthnagar, Ward 78, Bangalore – 560052 | Same |
| BBMP Khata No. | 59/141 | 59/141 |
| BBMP Municipal Sub No. | 59/141 | 59/141 |
| BBMP New Property ID | 7611897160 | 7611897160 |
| ULPIN | 2798962 | 2798962 |
| Super Built-up Area | 1,116 sq.ft. | 1,116 sq.ft. |
| Undivided Share | 1116/594862 (=574.17 sq.ft.) | 1116/594862 (=574.17 sq.ft.) |
| Car Parking | Slot 914 | Slot 914 |
| Land Area (parent) | 3,06,050 sq.ft. | 3,06,050 sq.ft. |

### Financials
| Field | ATS | Sale Deed |
|-------|-----|-----------|
| Total Sale Consideration | ₹2,25,00,000 | ₹2,25,00,000 |
| Token (03.02.2026) | ₹1,00,000 — Cheque 000148, Kotak Mahindra Bank, Infantry Rd, IFSC KKBK0008059 | Same |
| RTGS (05.03.2026) | ₹24,00,000, UTR: KKBKR52026030500983452 | ₹24,00,000, UTR: KKBKR52026030500983152 |
| RTGS (05.04.2027) | — | ₹75,00,000 + ₹1,25,00,000 |
| Seller Title Deed | GAN-1-00865-2012-13, June 2012 | Same |
| Encumbrance | SBI Loan A/c 64186230661 (to be discharged before SD) | SBI loan fully repaid, NOC issued |
| ATS Stamp Duty | ₹1,12,000 @ 0.5% | ₹1,12,000 @ 0.5% |

### Registration
| Field | ATS | Sale Deed |
|-------|-----|-----------|
| ATS Date | 05.03.2026 | — |
| ATS Doc No. | GNR-06465-2025-2026 | GNR-06465-2025-2026 |
| ATS Stamp Duty | ₹1,12,000 | ₹1,12,000 |
| SD Date | — | 05.04.2027 |

## UTR Discrepancy Note
ATS shows UTR ending `83452`; Sale Deed shows `83152`. The last 4 digits differ (`3452` vs `3152`). Both reference the same Kotak Mahindra Bank RTGS on 05.03.2026 for ₹24,00,000. **Recommend manual verification** with Kotak bank statement — likely an OCR misread of one document, but must be confirmed before filing.

## Session Workflow Used
1. `drive.files().get_media(fileId)` for ATS PDF (binary download)
2. `drive.files().export_media(fileId, mimeType='application/pdf')` for Sale Deed Google Doc (NOT `get_media` — would throw 403)
3. `pdf2image.convert_from_path(dpi=150)` → PIL Image per page
4. `vision_analyze` per page to extract all details
5. Build cross-reference table
6. Flag UTR discrepancy