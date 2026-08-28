# Court Order & Revenue Document Discovery in Drive

**Trigger:** A team member asks you to find a specific legal/revenue document known only by:
- A legal provision name (e.g. "Rule 43-J Confirmation Order", "Order 39 Rule 1 IA")
- A property/village name (e.g. Gunjur, Hurulagurki)
- A case number (e.g. OS 93/2019, Misc 210/2026)
- A description of the document's format ("looks like Old RTC")

The filename is NOT known. The document may be a scanned PDF with Kannada content.

## Multi-Phase Search Strategy

### Phase 1: Keyword Search Across Drive

Use `gws_skill_bridge.call("drive_search", ...)` with these parameter requirements:
- Always pass `raw_query=False` for plain-text search, `raw_query=True` for Drive-native query syntax
- Always pass `max=50` (or desired page size) — the bridge requires it to avoid SimpleNamespace AttributeError

Search patterns to try (run ALL, not just the obvious one):

| Category | Patterns |
|----------|----------|
| **Village name** | Search village name alone, common misspellings (Gunjur, Gujur, Gunjar), transliterations (Hurulagurki, Hurulgirki, Hulgurki) |
| **Document type** | "confirmation", "order", "CO", "rule", "43", "misc", "petition", "endorsement", "certificate" |
| **Survey number** | "Sy 93", "Sy.40", "Sy 93/2", "93-4", "136-4", survey numbers from known project docs |
| **Entity name** | Trust name (Godwad Bhavan, GBJT), company name, developer name |
| **Case number** | OS numbers, Misc numbers, WP numbers — both full and partial |
| **Project name** | Serenity Hillview, Serenity Hill View, Ranka [project], DRA [project] |

**Drive-native queries** (when raw_query=True):
```
name contains '43' and name contains 'order'
name contains 'CO' and name contains 'order'
name contains 'confirmation' and name contains '43'
```

### Phase 2: Inspect Folder Contents

When keyword search returns folder results, recursively inspect each folder:

```python
result = call('drive_search', query="'FOLDER_ID' in parents", raw_query=True, max=50, service_name='google-draas')
```

Look for files ending in:
- **"CO"** — likely stands for Confirmation Order (e.g. `93-4_136-4_CO.pdf`)
- **"Order"** or **"Order copy"** — court/revenue orders
- **"Endorsement"** — government endorsements on applications
- **"SD"** — Sale Deed (paired with "CO" sometimes)
- **Old RTC / Manual RTC** — handwritten tabular revenue records

### Phase 3: Check Index Spreadsheets

Many properties have **Google Sheets indexes** that list every document with links. Search for:
- "index" + village/survey name
- "checklist" + project name  
- "Legal Files Index" + location

These sheets are the fastest way to map a legal provision to a specific file.

### Phase 4: Content Verification

When keyword and folder searches don't yield an exact filename match:

**A. Text extraction (for text-based PDFs):**
```bash
pdftotext file.pdf - | grep -i "43\|confirmation\|order\|rule"
```

**B. Visual analysis (for scanned Kannada PDFs — most common):**
1. `pdftoppm -f 1 -l 1 -png -r 200 input.pdf /tmp/output_prefix`
2. Use `vision_analyze` with `also_describe_visually=true` asking about document type, format (tabular vs narrative), language, stamps, and whether it matches the target description

**C. Tesseract OCR for bulk Kannada:**
```bash
tesseract input.png output -l kan+eng
```

### Phase 5: Full-Text Survey Number + Village Search

When searching for **all documents related to a specific survey number in a specific village** (e.g. "Sy 39 in Gunjur"), use Drive's fullText query — it searches file metadata AND description fields, not just filenames:

```
fullText contains '39' and fullText contains 'Gunjur'
fullText contains '41' and fullText contains 'Gunjur'
```

**Combine with name-only search** for broader coverage:
```
(name contains '39' or name contains '41') and fullText contains 'Gunjur'
```

**Critical — use `build_service` directly from `terminal()`**, NOT `gws_skill_bridge.call("drive_search")`:
- The bridge has a known `SimpleNamespace AttributeError` bug with `raw_query` (passing `raw_query=False` or `raw_query=True` may still fail depending on the vault token path)
- execute_code sandbox cannot access the gws-vault Unix socket
- **Working pattern** — run Drive API calls directly from `terminal()`:

```bash
cd /opt/hermes && python3 -c "
from tools.gws_auth import build_service
import json
service = build_service('drive', 'v3', service_name='google-draas')
q = \"fullText contains '39' and fullText contains 'Gunjur'\"
fields = 'files(id, name, mimeType, modifiedTime, webViewLink)'
resp = service.files().list(q=q, pageSize=100, fields=fields).execute()
print(json.dumps(resp.get('files', []), indent=2, ensure_ascii=False))
"
```

**Multiple query passes** — run 5-8 different query variants in a single script to capture all relevant files:
1. `fullText contains '39' and fullText contains 'Gunjur'`
2. `fullText contains '41' and fullText contains 'Gunjur'`  
3. `(name contains '39' or name contains '41') and fullText contains 'Gunjur'`
4. `fullText contains 'Sy No 39'`
5. `fullText contains 'Sy No 41'`
6. `fullText contains 'Sy 39'`
7. `fullText contains 'Sy 41'`
8. `name contains 'Gunjur' and mimeType='application/vnd.google-apps.folder'` (find folders)

### Phase 6: Broaden Search

If not found in user's personal Drive:
- Check **shared/team drives** (though VK Das's account has none)
- Check **other Google accounts** (ndr@draas.com for DRAAS business docs)
- Check **Drive folder hierarchy** — the document may be in a parent folder not surfaced by narrow search terms

## Known Document Naming Patterns

| Pattern | Likely Meaning |
|---------|---------------|
| `*_CO.pdf` | Confirmation Order (revenue/court) |
| `*_SD.pdf` | Sale Deed |
| `*_EC.pdf` | Encumbrance Certificate |
| `*_MR.pdf` | Mutation Register extract |
| `*_RTC.pdf` | Record of Rights, Tenancy & Crops (Form 16) |
| `*_ILR_RR.pdf` | Index of Land Records + Record of Rights |
| `*_GPA.pdf` | General Power of Attorney |
| `*_SD_yyyy-mm-dd.pdf` | Sale Deed with date |
| `YYYYMMDD_*` | DRAAS filename convention with date prefix |

## "Looks Like Old RTC" — Document Format Guide

When a user says a document "looks like an old RTC", they mean:

- **Tabular format** with columns for: Survey Number, Extent (acres/guntas), Khata Number, Cultivator/Occupant Name, Paisari/Remarks
- **Handwritten** entries in Kannada
- **Form 16** (the official old RTC form number under Karnataka Land Revenue Rules)
- **Columns headed** in Kannada: ಸ.ನಂ, ವಿಸ್ತೀರ್ಣ, ಖಾತಾ ಸಂಖ್ಯೆ, ಸಾಗುವಳಿದಾರರ ಹೆಸರು, ಪೈಸಾರಿ, ಟಿಪ್ಪಣಿ
- **Official stamp** and signature of the Village Accountant/Tahsildar
- Multiple years on a single sheet (e.g. 1969-2003)

Documents that match this description include:
- Actual **old RTCs** (manual Form 16)
- **ILR (Index of Land Records)** — similar tabular format
- **Akkar Band** / **Akarabhand** — village land register extract
- **Record of Rights** — bound register pages
- **Confirmation Orders** on RTC format — a Revenue Inspector/Tahsildar's order confirming entries, often stamped onto an RTC-like form

## Form 43J (Rule 43) — Specific Discovery Notes

**Form 43J** is an extract under **Rule 43 of the Karnataka Land Revenue Act**, dealing with land transfer tracking and mutation records. It is NOT a standalone document type — it commonly appears **embedded inside multi-year RTC PDFs** alongside other revenue records (Form 16 RTCs, mutation registers, etc.).

### Form 43J Variants Found

Two document variants share the "Form 43J" label:

1. **Transfer/Incorporation Tracking Sheet** — Government compilation listing land transfers under Rule 43 for a survey number across a fiscal year. Contains: village, taluk, district, survey number, area, pending applications, incorporated area, cultivable area.
2. **Mutation / Khata Change Application** — Individual's application to mutate khata based on a registered sale deed. Contains: applicant name, seller, registration details, survey number, khata number, area, transaction type.

### Distinguishing Form 43J from Other Revenue Documents

| Looks Like | But Is Actually | Telltale Sign |
|-----------|----------------|---------------|
| Old RTC (Form 16) | Form 43J transfer tracking sheet | Has "Compilation List No." and "Pending Applications" column — RTCs don't have these |
| Mutation Register (Form 11) | Form 43J mutation application | Form 11 falls under **Rule 46**, NOT Rule 43. Form 43J deals with changes, Form 11 is the source ledger |
| "43-44" in filename | Financial Year 1943-44, not Form 43J | The dash indicates a FY range, not a form number. If paired with another year-like number (43-44, 44-45), it is a fiscal year reference, not a form reference |

### Multi-Year RTC PDFs — Form 43J is often INSIDE, not standalone

Typical PDF structure (e.g. "2002 to 2024 rtc SyNo 93.pdf"):
- Page 1: **Form 43J** — transfer/incorporation tracking sheet for the survey number
- Pages 2+: **RTC (Form 16) / Record of Rights** — ownership, tenancy, and crop data for each holder

Do NOT assume the file is "just an RTC" based on the filename. The first page(s) may be a Form 43J extract even though the file is named as an RTC.

### What to look for when examining a candidate document

Use Phase 4 content verification with these specific questions for vision_analyze:
1. **Is it a Form 43J?** Look for: Kannada title referencing "Rule 43", "Form 43J", compilation list numbers, or khata change application format
2. **What survey number(s) does it cover?** Key identifying field
3. **What year/range?** Form 43J covers a single fiscal year or a single transaction
4. **Is it bilingual?** English column headers with Kannada entries are common for post-digitization extracts
5. **Who are the parties?** For mutation applications, look for applicant/buyer/seller names

### Translation workflow for Kannada Form 43J

Due to handwritten Kannada entries and tabular layout, neither Tesseract nor vision_analyze OCR alone reliably extracts all data. Use this staged approach:

1. **vision_analyze** — identify document type, column headers, rough understanding of content
2. **OpenRouter Gemini 2.5 Flash** via `call_openrouter_model` — provide the image URL and ask for full translation of handwritten Kannada entries, column by column. Gemini 2.5 Flash handles Kannada script better than the default vision pipeline.
3. Prompt: *"This is a scanned Kannada Karnataka revenue document. Read ALL Kannada text visible, translate to English, identify document type (Form 43J / RTC / Mutation Register / Form 11 / EC), survey numbers, years, names, areas, and any other key data."*

### Parallel sub-agent examination

When you have multiple candidate PDFs, use `delegate_task` to analyze them in parallel — one sub-agent per document. Each runs independently (vision_analyze + OpenRouter translation + report), and all results return together.

```python
tasks = [
    {"goal": "Examine this scanned Kannada revenue document...",
     "context": "Image file: /path/file.png. Use vision_analyze then call_openrouter_model with gemini-2.5-flash...",
     "toolsets": ["vision"]},
    # ... one per document
]
results = delegate_task(tasks=tasks)
```

## Pitfalls

- **Scanned PDFs have no text layer** — pdftotext returns nothing; rely on pdftoppm + vision_analyze
- **Kannada OCR is unreliable** — Tesseract's Kannada model produces garbled output for handwritten entries; vision_analyze (Gemini Flash) is more reliable for document-type identification. For full translation of handwritten Kannada tabular data, use Gemini 2.5 Flash via OpenRouter.
- **"43-J" may not appear in filename** — The document may be named by case number, survey number, or date, not by the legal provision. Form 43J often appears inside multi-year RTC PDFs.
- **PDF -> PNG conversion speed** — pdftoppm at 200 DPI with 3+ pages can time out. Use 150 DPI with 1 page per call for safer performance, or run each page conversion as a separate command.
- **drive_search SimpleNamespace bug** — Always pass `raw_query=False` and `max=50` explicitly, or the bridge raises AttributeError
- **Multiple vendor folders** — Gunjur documents may be split across Gunjur Legal Files (OS cases), Gunjur Farm Dodballapur (revenue docs), and Downloads folder — search each separately
- **Confirmation =/= Confirmation Letter** — A "Confirmation Letter" from the Thasildar is an NOC letter format, NOT a tabular RTC-format confirmation order. Ask the user if the format is letter-style or RTC-style.
- **"10-43" / "4-43-44" notation** — The number "43" in a filename like Sy38_MR_4-43-44.pdf refers to the financial year 1943-44, NOT Form 43J. Always verify the context: if paired with another year-like number (43-44, 44-45), it is a fiscal year reference, not a form number.
