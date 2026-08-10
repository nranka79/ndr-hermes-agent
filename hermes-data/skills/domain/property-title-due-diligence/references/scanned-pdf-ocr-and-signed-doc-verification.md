# Scanned Legal PDFs — Read & Verify (pdftoppm + tesseract)

For signed/registered legal documents (JDAs, addenda, sale deeds, NOCs) that are image scans with **no text layer** — common in the Indian land-docs world.

## Symptom
- `pypdf`/`PyPDF2` extraction returns near-zero chars (e.g. "30 chars" for a 31-page deed) — that's a scanned PDF, not a corrupt file.
- Filenames/dates can be misleading: a file named `20241130 Signed Addendum 2` may actually contain a different document than its name implies — ALWAYS verify content by OCR, never trust the name.

## Recipe (no pypdf needed)
```bash
# 1. Render pages to PNG (first N pages to identify the doc, or all pages)
pdftoppm -png -r 100 -f 1 -l 3 input.pdf page      # produces page-01.png ...

# 2. OCR per page
tesseract page-01.png -                              # stdout text
# or sweep all pages into one file
for p in $(seq -w 1 31); do tesseract page-$p.png - 2>/dev/null; echo "===PAGEBREAK==="; done > full_ocr.txt
grep -i -n -E "second addendum|guruswamy|2025" full_ocr.txt
```
- `pdftoppm` and `tesseract` are available on the VPS at `/usr/bin/`. Render at 80–100 dpi for OCR; higher for fine print.
- If tesseract is missing: `apt-get install tesseract-ocr` (or use `vision_analyze` on the rendered PNGs as a fallback for single pages).

## Drive fullText search DOES index scanned PDFs
- `drive.files().list(q="fullText contains 'SECOND ADDENDUM' and mimeType='application/pdf'")` returns scanned PDFs — Google OCRs them server-side for search.
- BUT: matches are loose (Google's OCR may hit a phrase in a *different* bundled document inside a compilation PDF, e.g. a 31-page bundle containing e-stamp + addendum + sale deeds + a will). Always confirm with local tesseract OCR on the relevant pages before quoting a document as authoritative.

## Identification checklist for JDA addenda (Ranka Northstar / Allalsandra case)
1. List all addendum candidates: `name contains 'Addendum'` + `name contains 'North'/'Allasandra'` across mimeTypes (Google Doc drafts, docx drafts, scanned PDFs).
2. Distinguish DRAFT (Google Doc / docx, exportable to text) from SIGNED (scanned PDF, e-stamp page first).
3. The e-stamp page (first page) carries the **execution date** (e.g. "30-Nov-2024 03:44 PM", Article 5(J) Agreement) and parties — that's the ground truth for which version was actually executed.
4. Version chain for Northstar: Original JDA 07.02.2014 → First Addendum (drafts Aug–Nov 2024; **signed 30-Nov-2024 e-stamp**) → Second/Furter Addendum "Sharing for One Unit" (Sep 2025, only Google Doc drafts exist — NO signed PDF on Drive as of Aug 2026).
5. Read the signed PDF's operative clauses (title obligations, refundable deposits, FAR sharing) from OCR, and quote clause numbers — the user asks "what do the landowners owe me" and expects the amount + recovery mechanism from the *signed* document.

## Gmail threaded reply fallback (when skill bridge is unavailable)
If `tools.gws_skill_bridge` fails to import (its skill module lives under a permission-blocked dir), create the threaded draft directly via Gmail API:
- fetch the message being replied to → get its `Message-ID`, `References`, `In-Reply-To`, `threadId`
- build MIME with `email.mime.text.MIMEText`, set `To`, `Cc`, `Subject`, `In-Reply-To`, `References` (References = prior References + the message ID you reply to)
- `svc.users().drafts().create(userId='me', body={'message': {'raw': b64, 'threadId': tid}})`
- DRAFT ONLY — never `.messages().send()` (hard rule; always leave in Drafts for the human).
