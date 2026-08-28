---
name: byadarahalli-title-patterns
description: Karnataka property title due diligence patterns specific to Byadarahalli (Devanahalli Taluk) land aggregation by Satvik Developers. Covers Kannada KAVERI-format deed OCR workflow, survey number verification pitfalls, and two acquisition types (direct sale deed vs. agreement+GPA) with confirming party deed structure.
metadata:
  hermes:
    tags: [real-estate, title, byadarahalli, satvik-developers, kannada, ocr]
    category: domain
    related_skills: [legal-document-drafting, property-title-due-diligence, ocr-and-documents]
---

# Byadarahalli Title Patterns

Domain reference for Byadarahalli (Devanahalli Taluk) property title due diligence

## Kannada Document Extraction Workflow

### Sourcing the deed PDF from Google Drive (gws API)
When a shared link is a `drive.google.com/file/d/<FILE_ID>/view`, download the binary via the
Drive API — the plain `curl .../uc?export=download` returns HTML, and `files().get(fileId=..., alt='media')`
returns a dict (error), so use `MediaIoBaseDownload`:

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload
import io
drv = build_service('drive', 'v3', service_name='google-draas')  # resolve account first
fid = '...'
meta = drv.files().get(fileId=fid, fields='name,mimeType').execute()  # confirm it's a PDF
fh = io.FileIO('/tmp/deed.pdf','wb')
dl = MediaIoBaseDownload(fh, drv.files().get_media(fileId=fid))
done = False
while not done:
    status, done = dl.next_chunk()
```

These KAVERI-scan deeds are image-PDFs (no text layer). If `pdftotext` yields ~0 lines, render +
OCR: `pdftoppm -png -r 300 deed.pdf pgs/pg` then `tesseract pgs/pg-NN.png ocr/pg-NN` per page, and
concatenate with page markers. Read the whole concatenation — the survey-number ledger (Schedule A),
allocation (Schedules B/C), and recitals each span multiple pages.

For Kannada language KAVERI-format Agreement/GPA/Deed PDFs:

1. **pymupdf text extraction** usually produces garbled output (mixed Kannada/English encoding) - do not rely on it
2. **Google Docs PDF import** also produces garbled text - do not use this either
3. **Best approach:** Render pages as PNG images at 200 DPI (`page.get_pixmap(dpi=200)`) and use `vision_analyze` with task-specific questions
4. **Effective vision_analyze questions:**
   - "Read all amounts, dates, cheque numbers, and bank names" - for payment schedules
   - "Read ALL English text on this page" - for registration numbers, document IDs
   - "Find vendor/purchaser names and Aadhaar numbers" - for party identification
   - "Find the Schedule property description with East/West/North/South boundaries" - for boundary extraction
   - "Find the title flow and original ownership chain" - for recitals extraction
5. **Cross-reference with spreadsheet data:** The Byadarahalli Legal Docs spreadsheet (ID: `1aCTuKcDjH2t8G4ANyJkbhuXbXPPF7yWETQ3weQFsMN4`) has a Documents tab with vendor/purchaser details - but ALWAYS verify against actual PDF content as spreadsheet entries may contain incorrect/vendor-shortened names

## Survey Number Verification

**Critical pitfall:** A user may share document links for one survey number (e.g., Sy. 190/3 Agreement PDF) but actually want work done on a different survey number (e.g., Sy. 223).

- When a user shares both document links AND a Drive folder, check BOTH
- The folder contents often reveal the actual target property
- Always explicitly confirm the target survey number with the user before drafting any deliverable
- Separate documents shared for reference from the active property being dealt with

## Byadarahalli Acquisition Types

### Type A - Direct Sale Deed
Used for: Sy. 221/2, 176/2

- Satvik Developers purchased directly via registered Absolute Sale Deeds
- Title transferred from original owners (G. Bujjamma for 221/2, H.C. Sudha for 176/2) to Satvik Developers
- Partition Deed (SRJ-1-10373-2023-24) allocated these to C.R. Nagendra
- Standard 2-party sale deed: C.R. Nagendra (Vendor) to R3N KAAJ (Purchaser)
- Full title warranty from C.R. Nagendra

### Type B - Agreement + GPA (unregistered title)
Used for: Sy. 223

- Agreement to Sell directly in C.R. Nagendra's personal name
- Irrevocable GPA from original owners to Satvik Developers (C.R. Nagendra as partner)
- Title still legally with original owners; beneficial rights vested in C.R. Nagendra through Partnership Deed allocation
- Confirmatory sale deed structure needed rather than standard 2-party deed
- Vendor covenants modified: "entitled by virtue of Agreement + GPA + Partition Deed" not "absolute owner"

## Sy. 223 Reference Data

- **Extent:** 2-00 Guntas, Sy. 223 (Old Sy. 18), Byadarahalli Village
- **Vendors (original):** Smt. Munithayamma, Sri. Arun M (grandson) + 37 legal heirs of Late Naikara Thimmaiah @ Thimmappa
- **Agreement:** DNH-1-12781-2022-23 dated 11-01-2023, C.R. Nagendra = Purchaser
- **Total Consideration:** Rs. 1,62,00,000 (advance Rs. 1,00,00,000 paid; balance Rs. 62,00,000)
- **GPA:** DNH-4-01083-2022-23 dated 11-01-2023, 37 heirs to Satvik Developers (C.R. Nagendra)
- **Boundaries:** E = Siddappanna's Muniyappa's land, W = Munishamappa's land, N = Gomala land, S = Anjinappa's land
- **Title chain:** Naikara Thimmaiah -> 37 legal heirs -> Prior Agreement 17-05-2013 (cancelled) -> GPA+Agreement 11-01-2023 -> Partition Deed 16-01-2024 -> C.R. Nagendra
- **Ashok Kumar contribution:** Rs. 5.5 Cr paid during Satvik Developers subsistence, recorded as acknowledgment in Partition Deed

## Partition Deed Allocation (SRJ-1-10373-2023-24)

The 16-Jan-2024 partition deed is the master ledger for who owns what. Fuller detail in
`references/partition-deed-srj-10373-allocation.md` (full 22-item Schedule A/B/C table +
agreement/pending/litigation rights). Key facts:
- Schedule A = 22 items (18 Byadarahalli + 118/2, 7/3, 7/9 at Sarjapura + 185 at Gunjur/Varthur)
- **Schedule B → Ashok Kumar (Partner No.1, 90%):** 20 items — all except 221/2 and 176/2
- **Schedule C → C.R. Nagendra (Partner No.2, 10%):** 2 items — Sy. 221/2 (3A 38G kharab), Sy. 176/2 (1A 20G)
- All rights under agreements/GPAs/JDAs + pending-registration + litigation/non-mutated numbers
  (209/1-4, 210, 111/1, 42/1, 47/2) settle to Ashok Kumar
- Therefore the Type A sales (221/2, 176/2) are the ONLY ones vendored by C.R. Nagendra in his
  own name — everything else traceable to Ashok Kumar's 90% block