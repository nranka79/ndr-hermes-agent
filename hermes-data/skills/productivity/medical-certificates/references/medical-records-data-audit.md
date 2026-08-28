# Medical Records Data Audit — Cross-Document Field Search

**Trigger:** User asks "check all reports for [specific data point]" — e.g., blood group, diagnosis date, vaccination status, specific lab value — across the patient's entire medical folder.

This is **distinct** from `missing-medical-report-cross-document-search.md`, which searches for a missing standalone PDF report. This audit searches WITHIN all existing documents for a particular field/value.

## Workflow

### Phase 1 — Clarify the Target

Confirm with the user:
- **What data point?** (blood group, HbA1c value, FEV1%, vaccination date, etc.)
- **Which patient?** (KDR, NDR, Ruhaan, etc.) — scope the folder(s)
- **Any time window?** (all records, or only last N years)
- **Include invoices?** Invoices rarely carry clinical data, but the user may want them checked for service descriptions (e.g., "Blood Grouping" as a billed item)

### Phase 2 — Inventory All Files

List all files in the patient's medical folder (and the Invoices subfolder):

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

# Get all files from medical folder + invoices subfolder
folder_ids = [MEDICAL_FOLDER_ID, INVOICES_FOLDER_ID]
all_files = []
for fid in folder_ids:
    page_token = None
    while True:
        res = drive.files().list(
            q=f"'{fid}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, size, createdTime)",
            pageToken=page_token
        ).execute()
        all_files.extend(res.get('files', []))
        page_token = res.get('nextPageToken')
        if not page_token:
            break

# Sort by name (usually chronological with YYYYMMDD prefix)
all_files.sort(key=lambda f: f['name'])
```

### Phase 3 — Classify by Content Relevance

Not every file needs full text extraction. Classify from filename:

| Filename pattern | Likely relevance for data audit |
|---|---|
| `Blood Test`, `Hb`, `CBC`, `Hemogram`, `Biochem`, `Thyrocare`, `Aarogyam` | **High** — likely contains the target if it's a lab value or blood group |
| `HealthCheck`, `Medical Checkup`, `Master Health` | **High** — comprehensive panels often include blood group |
| `Consultation Advice`, `Prescription`, `OPD` | **Medium** — may mention planned tests, rarely have actual results |
| `ECG`, `X-ray`, `Ultrasound`, `2DEcho`, `ChestXray` | **Low** — imaging reports, unlikely to contain blood group/general labs |
| `Invoice`, `Bill`, `Receipt` | **Low** — only relevant if the target was a service billed (e.g., "Blood Grouping" item on invoice) |
| `Compilation`, `Summary`, `Index` | **High** — aggregated documents may include all known values |

For each high/medium file, extract text (pdftotext or pymupdf) and search for the target.

### Phase 4 — Batch Text Extraction

Use a structured approach — don't open every file manually:

```python
import fitz
import re

targets = ['blood group', 'bld grp', 'blood grouping', 'bg', 'abo', 'rh', 'a+', 'b+', 'ab+', 'o+', 'a-', 'b-', 'ab-', 'o-']
found = []

for f in all_files:
    # Download
    request = drive.files().get_media(fileId=f['id'])
    content = request.execute()
    local_path = f'/tmp/audit_{f["id"]}.pdf'
    with open(local_path, 'wb') as fh:
        fh.write(content)

    # Extract text
    doc = fitz.open(local_path)
    text = ""
    for page in doc:
        text += page.get_text()

    # Image-based PDF fallback
    if len(text.strip()) < 50:
        # Try OCR via pdftotext
        import subprocess
        result = subprocess.run(['pdftotext', local_path, '-'], capture_output=True, text=True, timeout=30)
        text = result.stdout or text

    # Search
    text_lower = text.lower()
    for t in targets:
        if t in text_lower:
            # Extract the line containing the match
            for line in text.split('\n'):
                if t in line.lower():
                    found.append({'file': f['name'], 'match': line.strip(), 'pattern': t})
                    break
            break  # One match per file is enough

    doc.close()
```

### Phase 5 — Report Findings

Always report in this structure:

```
**Data point searched:** [target]

**Files examined:** [N] total ([M] high/medium relevance, [K] low relevance)

**Files with matches:**
- [filename] — "[matched line]"

**Files where it was expected but not found:**
- [filename] — the test was prescribed here but not present in the results

**Files checked (no match) — key blood/report files:**
- [filename] — [list of what it actually contained]
- [filename] — [list of what it actually contained]

**Conclusion:**
✅ / ❌ Blood group found in [N] file(s)
[If not found: actionable next steps]
```

### Phase 6 — Gap Analysis

If the test was **prescribed** (on a Consultation Advice or Prescription) but **not found** in any report:

1. Check the **Invoice** for the same date — does it list the test as a billed item?
2. If **not billed** → the test may not have been done yet (common when the doctor prescribes it but the lab hasn't processed it yet, or the patient skipped that test)
3. If **billed** → the report may be missing from Drive (see `missing-medical-report-cross-document-search.md`)

### Phase 7 — Actionable Next Steps

If the data point is **not found**, suggest concrete actions:

- **"The test was prescribed on [date] by Dr. [name] but not included in the billed lab tests"** — suggest getting it done at the next visit / pre-op workup
- **"The test was on the invoice but no report is uploaded"** — ask the hospital for the report
- **"The blood work reports don't include this as a standard panel item"** — some labs require a specific request for blood group; it's not always automatic with blood counts
- **"Check with the hospital's front desk / lab"** — they can run it as a standalone test in 5 minutes

## Real Example (Jul 2026)

| Detail | Value |
|--------|-------|
| Target | Blood group for KDR |
| Scope | KDR Medical (root) + KDR Invoices |
| Files checked | 82 (15 blood/test reports, 7 invoices, 60+ low-relevance images/receipts) |
| Prescribed? | Yes — Dr. Haldipur's Consultation Advice listed "Blood Grouping" |
| Billed? | **No** — the lab invoice (Rs 15,730) did NOT include blood grouping |
| Result | Not found in any file |
| Advice | Get it done at Trustwell during pre-op workup for ear surgery (15 Jul 2026) |

## Pitfalls

- **Don't confuse "test name" with "test result"** — A consultation advice may say "Blood Grouping" as a prescribed test but the actual result wasn't documented in any report yet
- **Don't assume all blood panels include blood group** — Many standard lab panels (CBC, HbA1c, Lipid, LFT, KFT) do NOT automatically include blood group. It's often a separate order
- **Don't overlook invoices** — The invoice may list "Blood Grouping" as a billed item even though the report isn't uploaded yet. This tells you the test was done, and you should ask for the report
- **Voice transcription noise** — The user's voice may say "PTA research" (Pure Tone Audiometry) when they mean a different test. Always trust the document content over the voice transcription
- **Large folder sizes (50+ files)** — Batch process in groups. Use filename patterns to classify relevance before extracting every document
- **Image-only scanned PDFs** — Some old reports are scanned images. pdftotext returns empty; use pdftoppm + OCR as fallback only when the filename suggests the report type is relevant
- **Invoice descriptions are billing line items, not clinical results** — An invoice item "Blood Grouping" means it was charged, not that the result is on the invoice. The report is a separate document
