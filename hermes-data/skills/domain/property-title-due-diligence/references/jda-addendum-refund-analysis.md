# JDA Addendum — Signed-vs-Draft & Landowner Refund Math

Trigger: "as per the JDA addendum, what do the landowners owe / refund", "find the signed
addendum", "update the landowner on the refundable deposit".

## 1. Locate the SIGNED PDF, not the draft
- Drive typically holds BOTH: drafts as Google Docs (or .docx) and the executed copy as a
  scanned PDF (often named `YYYYMMDD Signed Addendum ...pdf`).
- Signed PDFs usually start with an **e-stamp / non-judicial stamp certificate on page 1**
  carrying the TRUE execution date. Do NOT trust the filename date alone — render page 1
  (`pdftoppm -png -r 100 -f 1 -l 1 file.pdf page`) and OCR it (`tesseract page-01.png -`)
  to read the e-stamp date and the "Addendum to JDA dated ..." line.
- A "Further Addendum / Second Addendum" drafted later (e.g. Sep 2025) may still be
  **unsigned** — state that explicitly; the signed PDF is the binding document.
- Google Drive fullText search can surface phrases inside scanned PDFs (Drive OCR-indexes
  them), e.g. `q="fullText contains 'SECOND ADDENDUM TO JOINT DEVELOPMENT'"` — useful to find
  whether a signed bundle contains a particular clause. Confirm with your own OCR before relying.

## 2. Extract the refundable-deposit position
From the signed addendum read:
- acknowledged refundable deposits paid to date (e.g. ₹2.40 Cr)
- additional refundable items treated as deposits (e.g. ₹50L pipeline-shift costs)
- total refundable (e.g. ₹2.90 Cr)
- recovery mechanism: 100% of initial sale revenues from identified inventory, collateralized /
  encumbered in favour of the developer; developer may sell inventory to recover dues.
- sharing ratio: owners get 33% of 1.75 FAR BUA; only 15% of super BUA from any FAR above 1.75.

## 3. Per-landowner refund math
- total_refundable × owner_share% = owner's refundable contribution
  e.g. ₹2,90,00,000 × 11.43% = ₹33,14,700 (~₹33.15L)
- net = incoming consideration − owner's contribution
  e.g. ₹1.75 Cr − ₹33.15L = ₹1,41,85,300 (~₹1.42 Cr net)
- Verify the owner's share % from context (user dictates it; e.g. Sundar Padmanabhan 11.43%,
  Site 4). Present the arithmetic inline in the message — the user wants the calculation shown.

## Session anchor
Ranka Northstar, Allalsandra. Signed PDF: `20241130 Signed Addendum 2 JDA Allalsandra
Site No 1 to 8 (DRA Ranka Holdings).pdf` (e-stamp 30-Nov-2024) — file id
1YPxHTClsPiKSqenUA09o0OdZdBcC398S. Sep 2025 "Further Addendum (Sharing for One Unit)" exists
only as Google Doc draft — unsigned. Sundar Padmanabhan WhatsApp +91 98204 35939.
