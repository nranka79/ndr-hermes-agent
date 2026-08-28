# Section 281 Application — Form Filling via Google Docs API

**Trigger:** User needs to update or create an Income Tax Section 281 application (prior approval for transfer of assets where there may be outstanding tax demands) for a partner contributing land to a partnership firm.

## Context

Section 281 of the Income-tax Act, 1961 requires prior approval from the Assessing Officer before a person transfers assets (land, shares, etc.) when there is a pending tax demand or the transfer could defeat tax recovery. For DRAAS, this arises when:

- A land-owning partner contributes immovable property to a partnership firm as capital
- The contribution transfers "possession" within the meaning of Section 281
- Separate applications are needed **per partner and per property category** (e.g., Palya land vs Byadarahalli lands for the same partner)

## Document Structure (Standard)

```
24 June 2026

From,
[PARTNER NAME]
PAN: ________
[Address]

To,
THE ASSESSING OFFICER
Circle ____(____)
[Address of AO Office]

SECTION 1 — DETAILS OF THE APPLICANT
  Name, PAN, Residential Status, Address, Phone, Email

SECTION 2 — DETAILS OF THE PROPOSED TRANSACTION
  Name of Firm, Partnership Date, Partners, Profit Share, Nature of Contribution

SECTION 3 — DESCRIPTION OF THE LAND ASSETS
  Schedule A / Schedule B with survey numbers, extents, villages, boundaries, valuation

SECTION 4 — TAX COMPLIANCE HISTORY
  ITR filing details for AYs 2022-23, 2023-24, 2024-25

SECTION 5 — DECLARATION REGARDING TAX DEMANDS

SECTION 6 — PRAYER

Enclosures: ITR acknowledgements, tax demand screenshot, partnership deed, sale deeds
```

## Workflow — Filling an Existing Google Doc Template

### Step 1 — Read the template

```python
from tools.gws_auth import build_service
import re

docs = build_service('docs', 'v1')
doc = docs.documents().get(documentId=DOC_ID).execute()
content = doc.get('body', {}).get('content', [])
text_parts = []
for el in content:
    for para in el.get('paragraph', {}).get('elements', []):
        tr = para.get('textRun', {})
        if tr.get('content'):
            text_parts.append(tr['content'])
full_text = ''.join(text_parts)

# Identify all placeholders
placeholders = re.findall(r'\[[^\]]+\]|_{2,}', full_text)
```

### Step 2 — Fill known fields with replaceAllText

**Do NOT attempt index-based manipulation** for simple replacements. Use `replaceAllText` — it's content-based and immune to index shift errors:

```python
requests = []

requests.append({
    'replaceAllText': {
        'containsText': {'text': '[PAN: ________________]', 'matchCase': True},
        'replaceText': 'PAN: ANBPK6960D'
    }
})

requests.append({
    'replaceAllText': {
        'containsText': {'text': '[Address Line 1]', 'matchCase': True},
        'replaceText': 'No. B-27, Zonasha Paradiso'
    }
})

# ... more replacements ...

docs.documents().batchUpdate(
    documentId=DOC_ID,
    body={'requests': requests}
).execute()
```

**Limitations:**
- Each `replaceAllText` replaces ALL occurrences of the search string — use unique placeholders
- Case-sensitive unless `matchCase: false`
- Cannot change formatting (only text content)
- Works across paragraphs and tables

### Step 3 — Fields that typically need user input

| Field | Source | Status |
|-------|--------|--------|
| PAN | Known from partnership deed/reconstitution deed | Fillable |
| Address | Known from dissolution deed or deed docs | Fillable |
| Phone / Email | User must provide | Ask user |
| AO Circle & Ward | Varies by jurisdiction | Ask user |
| Father's name | From partnership deed | Fillable |
| CIN of DRA Realty | Known from older docs (U70100KA2011PTC058105) | Pre-fill if found |
| ITR data (AYs, dates, income) | From user's tax records | Ask user |
| Property descriptions | From reconstitution deed Schedule A/B/C | Pre-fill from deed |
| Tax demand status | User must confirm | Ask user |

## Splitting — When to Create Separate Applications

The user may want **separate Section 281 applications** per property category (e.g., Palya vs Byadarahalli) even though the template combines both. In that case:

1. Copy the template: `drive.files().copy(fileId=SOURCE_ID, body={'name': 'New Name'}).execute()`
2. Keep only the relevant Schedule section in each copy
3. Update each copy with the specific partner/property details

## Source Documents for Extracting Details

| Detail | Source Document |
|--------|----------------|
| Partner name, address, father's name | Dissolution deed |
| PAN, Aadhaar | Reconstitution deed (where `PAN [PartnerName]` appears) |
| Property survey details | Reconstitution deed Schedules A/B/C |
| Partnership date, profit ratio | Reconstitution deed |
| CIN of DRA Realty | Reconstitution deed (first WHEREAS clause) |

## Finding Signed Copies on Drive

When the user asks "do we have signed copies of the Section 281 applications?" — the signed PDFs may not have "281" or "Section 281" in their filename. They are scanned image PDFs (not Google Docs) stored in a subfolder.

### Signed-Copy Search Pattern

1. **Check for a `Signed Documents` subfolder** inside the project folder. This is where executed/scanned signed PDFs are stored.

2. **Search by alias filename.** The signed 281 applications are typically named `[Name] - letter to AO ITD.pdf` (e.g., `Ashok Kumar - Letter to AO ITD.pdf`, `Satvik Developers - letter to AO ITD.pdf`) rather than including "Section 281" in the name.

3. **Search broadly with name-alternative queries:**
   ```python
   results = drive.files().list(
       q="name contains 'Letter to AO' and trashed=false",
       fields='files(id, name, parents)'
   ).execute()
   ```

4. **Check subfolders recursively** — list all children of the project folder, identify subfolders by mimeType, and inspect their contents.

### Verifying Signed Copies via OCR

Since signed PDFs are scanned images (not text-layer PDFs), OCR them to verify which lands/applicant they cover:

```python
import fitz, subprocess, io, os
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload

drive = build_service('drive', 'v3')
request = drive.files().get_media(fileId=SIGNED_FILE_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/signed.pdf', 'wb') as f:
    f.write(fh.getvalue())

doc = fitz.open('/tmp/signed.pdf')
for i in range(len(doc)):
    pix = doc[i].get_pixmap(dpi=200)
    pix.save(f'/tmp/page_{i}.png')
    result = subprocess.run(
        ['tesseract', f'/tmp/page_{i}.png', 'stdout', '-l', 'eng', '--psm', '6'],
        capture_output=True, text=True, timeout=60
    )
    print(f"--- Page {i+1} ---")
    print(result.stdout[:2000])
    os.remove(f'/tmp/page_{i}.png')
doc.close()
os.remove('/tmp/signed.pdf')
```

**Key things to verify via OCR:**
- Applicant name (matches expected partner/entity)
- Which Schedule(s) are included (Palya, Byadarahalli, or both)
- Whether multiple draft applications were **combined into one signed PDF** (common practice)

### Real-World Example (DRA KAAJ, Jun 2026)

| Item | Draft Doc (Google Doc) | Signed Copy (PDF in Signed Documents) |
|------|----------------------|--------------------------------------|
| Ashok Kumar — Palya | `20260624_AshokKumar_Sec281_Application_DRA_KAAJ` | `20260624 Ashok Kumar - Letter to AO ITD.pdf` (✅ covers BOTH Palya + Byadarahalli in one combined 5-page app) |
| Ashok Kumar — Byadarahalli | `20260624_AshokKumar_Sec281_Application_DRA_KAAJ_Byadarahalli` | *(superseded — combined into single app above)* |
| Satvik Developers — Byadarahalli | `20260624_SatvikDevelopers_Sec281_Application_DRA_KAAJ_Byadarahalli` | `20260624 Satvik Developers - letter to AO ITD.pdf` (✅ covers Byadarahalli only) |

**Lesson:** Even when separate draft docs exist per partner per property category, the signed version may merge them. Always OCR-verify the signed PDF to determine actual scope rather than assuming the draft structure was preserved.

### Signed Documents Folder Contents (DRA KAAJ Pattern)

The `Signed Documents` subfolder typically contains other executed documents alongside the 281s:

| Document | Typical Name Pattern |
|----------|---------------------|
| Deed of Reconstitution | `YYYYMMDD [Firm] - Deed of Reconstitution of Partnership.pdf` |
| Contribution Deed — Palya | `YYYYMMDD [Firm] - Contribution Deed - Palya Land.pdf` |
| Contribution Deed — Byadarahalli | `YYYYMMDD [Firm] - Contribution Deed Byadrahalli lands.pdf` |
| Capital Withdrawal Request | `YYYYMMDD [Firm] [Name] Request letter for Withdrawal of Excess Capital.pdf` |
| Payment Voucher | `YYYYMMDD [Name] payment vouchure and Check issued details.pdf` |
| **Section 281 (signed)** | `YYYYMMDD [Name] - Letter to AO ITD.pdf` |

## Pitfalls

- **"Don't create new versions"** — The user explicitly prefers editing the existing document in place rather than creating v2/v3/updated copies. Use `replaceAllText` to modify the existing doc.
- **PAN field appears in multiple places** — The header "[PAN: ____________]", the sub line "PAN: [________]", and the signature block "PAN: [________]" all need separate replacement calls if they use different placeholder text.
- **Property schedule from reconstitution deed** — The reconstitution deed typically lists all properties in Schedules. Verify which properties belong to which partner before filling the application. The Partition Deed (which divides assets between partners after dissolution) is the authoritative source for who owns what.
- **Multiple Section 281 apps may be needed** — One per partner per property category. The template combines everything; ask the user if they want to split.
- **Filename mismatch between drafts and signed copies** — Signed PDFs use "Letter to AO ITD" naming, not "Section 281 Application". Searching by the draft name will miss the signed version. Always check the `Signed Documents` subfolder and search for "Letter to AO" as an alias.
- **Combined vs split in practice** — Even when the user asks for separate applications per property (Palya vs Byadarahalli), the signed version may merge them into one. Verify via OCR before reporting what exists.
