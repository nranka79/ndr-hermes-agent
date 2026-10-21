# Customer / Case Evidence Pack from Gmail + Drive (worked 2026-09-09/10, Mirabilis B1-203 "Sabyasachi Behera" CMP/200628/0006093)

When NDR says "build an evidence pack for this customer/case — pull the emails and drive docs, keep only what relates to them" the full pipeline below is proven. The pack lives on Drive; the work happens on the server.

## Pack layout (Drive folder, e.g. `20260909 Mirabilis RERA Case ... (CMP ...)`)
- `README.md`, `INDEX.csv`, `Manifests/` (per-account .eml metadata)
- `Documents_Collected/` — relevant PDFs/sheets only
- `Emails_<account>/` — original .eml files
- `Emails_<account>/Readable_Emails/<email_folder>/` — per-email folder: `<name>.pdf` (readable render), `email.txt`, `Attachments/`
- Provenance folders for docs pulled from OTHER people's drives: `Documents_From_<Name>_Drive/`, `Emails_From_<Name>_Fwd/`

## Emails → readable PDF + attachments (the core converter)
Input: 1,989 .eml files (Gmail takeout or exported folders). Output per email folder, verified 2026-09-09.

1. **Parser**: Python `email` module. For each .eml: headers (From/To/Cc/Date/Subject) → HTML or plain body → render; strip attachments to real files (`msg.get_payload()`, decode `get_payload(decode=True)`, write binary with `get_filename()` name).
2. **Renderer: WeasyPrint** (Python lib, already installed) — `HTML(string=body).write_pdf(...)`. Handles Gmail HTML, inline cid images, quoted replies. DO NOT use the Playwright/Chrome binary on this box: the installed Chrome is an ARM build that core-dumps on x86 — WeasyPrint is the reliable renderer.
3. **RecursionError on deeply-nested marketing HTML**: WeasyPrint crashes with `RecursionError: maximum recursion depth exceeded` on newsletter-style emails (deeply nested tables). Fix (verified — repaired all 122 failures): run the render inside a big-stack thread and raise the limit:
   ```python
   import threading, sys
   def _run():
       sys.setrecursionlimit(20000)
       HTML(string=body).write_pdf(out)
   t = threading.Thread(target=_run, args=(), kwargs={})  # default stack ok; if still failing use stack_size
   ```
   If recursion still trips, spawn the render in a thread with a large stack: `threading.stack_size(512*1024*1024)` before starting. Do NOT lower to plain-text fallback first — big-stack + high recursion limit works.
4. **Plain .txt sibling** (`email.txt`) for fast grepping — also the answer to "I can't view .eml, make readable PDFs".
5. **INDEX.csv** at root: account, date, sender, receiver, subject, attachment names/counts, `behera`-style relevance flag. Build by parsing each email's headers; add `flag` via keyword match on subject+body.
6. **Account grouping bug to avoid**: when converting, pass the PACK root (parent dir of account subdirs) as `--src`, NOT a single account subdir — otherwise every email lands under "misc" instead of its account folder.
7. Parallelize with `multiprocessing`/`executor` workers (3 worked; ~0.12 s/email at 3 workers, 1,989 emails ≈ 5 min).

## Relevance cleanup — BODY-LEVEL, not filename-level
First cleanup pass used filename/metadata only and let unrelated mail through (A-1001 demand notes, Ipsita Behera flat A-1002, Tata CLiQ jewellery ad). The re-cleanup (verified) reads `email.txt` for each email and matches on the customer's real names, unit, case number, PAN, and email addresses:
- Keep only: named-customer correspondence, their unit (B1-203), their case (CMP/200628/0006093), banking inflow details with their name.
- Multi-customer lists (Agreements Sheet, Registrations, Booking Details, payment credits/debits, TDS) stay ONLY if the customer's row is present.
- Exclude: same-surname DIFFERENT customers (Ipsita Behera = flat A-1002), brand artifacts (Sabyasachi Couture), project-level documents with no customer name, neighbour flats (B1-201), generic 1-page floor plans.
- Same rule applied to Documents_Collected: read EVERY file (pdftotext + OCR for scans, cell-level for every spreadsheet, docx/doc extraction, JSON sniff on .bin), search for customer/unit/case markers, trash non-matches. Trash (recoverable), never hard-delete.

## Sandbox rules that mattered
- Google API client in threads = segfault; use **process-level sharding** (8 parallel processes) for uploads, not threads.
- Upload via NDR's own token (`build_service("drive","v3",service_name="google-draas")` + `MediaIoBaseUpload`), pre-create target folders.
- After cleanup, RE-CHECK for ghost folders: a stray earlier uploader can keep creating dirs mid-cleanup (420 ghost dirs in one run) — re-inventory after trash pass and repeat until clean.
- Empty-folder sweep: recursive walk, trash folders with zero remaining children, repeat to fixpoint (deleting an empty folder can empty its parent). Also check folders whose children are ALL trashed (look empty in UI; need trash-side check).
- Dedupe before copying from another user's drive: compare text length/content hash against what's already in the pack (identical Agreements Sheet 14,015 chars / Registrations 4,922 chars = skip).

## Links
- DWD access to colleague drives: see `gws-automation` skill `references/dwd-colleague-access.md`.
- OCR pipeline for the scanned 60-page Agreement of Sale: `pdftoppm -png -r 150` + `tesseract` (or ocrmypdf) from `ocr-and-documents`.