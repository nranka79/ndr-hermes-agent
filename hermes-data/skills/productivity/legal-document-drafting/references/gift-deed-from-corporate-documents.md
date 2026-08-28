# Gift Deed Creation from Corporate Documents

Create a consolidated gift deed for shares in multiple family/group companies, extracting shareholding data from Share Transfer Agreements (SHAs) and Family Settlement Deeds on Google Drive.

## Workflow

### 1. Discover Source Documents on Drive

Search for SHA documents and Family Settlement/Arrangement Deeds:

```python
drive = build_service('drive', 'v3')

# Find SHAs
results = drive.files().list(
    q="name contains 'Share Transfer' or name contains 'Family Settlement' or name contains 'Family Arrangement'",
    spaces='drive', fields='files(id, name, mimeType, parents, webViewLink)',
    pageSize=50
).execute()
```

**Common locations:**
- `Family/` — Google Doc versions of SHAs (v2, v4/final)
- `Final Docs JUN2020/` — Signed final versions of SHAs
- `DR DDR Fmly Signed Docs/` — Signed PDF bundles per company (e.g., `drap docs.pdf`, `scpl documents.pdf`)
- `Family Settlement - Final - 2025/` — The comprehensive Family Arrangement Deed (scanned PDF)

### 2. Extract Shareholding Data

**From Google Doc SHAs (via Docs API):**

```python
docs_svc = build_service('docs', 'v1')
doc = docs_svc.documents().get(documentId=DOC_ID).execute()

# Extract paragraph text
for el in doc['body']['content']:
    if 'paragraph' in el:
        for para_el in el['paragraph']['elements']:
            if 'textRun' in para_el:
                text += para_el['textRun']['content']

# Extract table data (Schedules A/B)
for el in doc['body']['content']:
    if 'table' in el:
        for row in el['table']['tableRows']:
            cells = []
            for cell in row['tableCells']:
                cell_text = ''
                for cell_el in cell['content']:
                    if 'paragraph' in cell_el:
                        for elem in cell_el['paragraph']['elements']:
                            if 'textRun' in elem:
                                cell_text += elem['textRun']['content']
                cells.append(cell_text.strip())
```

**Key data to extract:**
- Schedule A (pre-transfer shareholding table)
- Schedule B (post-transfer shareholding table)
- Identify the Donor's holding in each company

**From scanned Family Settlement PDFs (via OCR):**

```bash
# Convert PDF to images, then OCR
pdftoppm -r 200 -png /tmp/deed.pdf /tmp/pages/page
tesseract /tmp/pages/page-01.png stdout -l eng
```

Pitfall: OCR quality varies. Search for company names, share counts, and Nishant/NDR references. The key sections are usually "SCHEDULE OF DR ESTATE ASSETS AND FINAL ENTITLEMENT" / Annexure F.

### 3. Determine Current Shareholding

Cross-reference SHA data with Family Settlement allocations:

| SHA Source | Shows | Family Settlement Shows | Result |
|-----------|-------|----------------------|--------|
| 2020 SHA Schedule B | Post-Kanta→Dharmesh transfer | Additional Mamata→NDR/MDR/DDR allocations | Updated total per company |

**Example — DRA Projects:**
- 2020 SHA Schedule B: Nishant = 2,000 shares (20%)
- 2025 Family Settlement Clause 5.2.1: Mamata transfers 527 shares to Nishant
- **Current total: 2,527 shares**

**Clause 3.1 supersession rule:** The 2020 documents prevail over the 2025 Deed unless the matter is specifically carved out in Clause 3.2. Check whether the share allocation is a "carved-out" matter (DRA Projects Mamata→NDR/MDR/DDR was carved out; DRA Developers and Southcity were not).

### 4. Draft the Gift Deed

**Use HTML-to-Google-Doc import** (not Docs API batchUpdate) for professional formatting — see `google-doc-formatting-template` skill for the import script pattern.

**Essential clauses under Indian law for a share gift deed:**

| Clause | Purpose | Legal Basis |
|--------|---------|-------------|
| Donor identity, capacity, address | Identify the transferor |—|
| Donee identity, relationship, address | Identify the transferee |—|
| Recitals: ownership, relationship, sound mind, love/affection, acceptance | Show consideration and competency | S.122 TPA |
| **GIFT** operative clause | Transfer of property | S.122–S.126 TPA |
| **ACCEPTANCE** | Donee's acceptance (must be during donor's lifetime) | S.122 TPA |
| **TITLE AND WARRANTIES** | Donor warrants good title, no encumbrances | S.55(2) TPA |
| **TRANSFER OF SHARES** | Donor to execute transfer forms, apply to companies | Companies Act 2013 |
| **ABSOLUTE GIFT** | Donee holds free of donor's claims | S.126 TPA |
| **INDEMNITY** | Donor indemnifies for title defects | Contractual |
| **COSTS AND EXPENSES** | Who bears stamp duty, registration | Recommended |
| **REGISTRATION** | Present for registration under Registration Act 1908 | S.123 TPA (optional for movable, recommended for enforceability) |
| **GOVERNING LAW AND JURISDICTION** | Laws of India, exclusive Bangalore courts | Recommended |
| **SEVERABILITY** | Partial invalidity doesn't affect rest | Standard boilerplate |
| **ENTIRE AGREEMENT** | Supersedes prior agreements | Standard boilerplate |
| **SCHEDULE** | Table listing each company, share count, percentage, CIN | Essential |
| **SIGNATURE** | Donor + Donee | S.122 TPA |
| **WITNESSES** | Two attesting witnesses | S.123 TPA |

**HTML template for the Schedule table:**

```html
<table style="width:100%;border-collapse:collapse;font-size:11pt">
<tr style="background-color:#1a1a2e;color:#fff">
  <th style="border:1px solid #000;padding:8px;text-align:center">Sl.No</th>
  <th style="border:1px solid #000;padding:8px;text-align:left">Company Name</th>
  <th style="border:1px solid #000;padding:8px;text-align:center">Shares</th>
  <th style="border:1px solid #000;padding:8px;text-align:center">%</th>
  <th style="border:1px solid #000;padding:8px;text-align:left">CIN</th>
</tr>
<!-- data rows with alternating bg: #f7f7f7 / white -->
<!-- total row with bg: #d4edda (green tint) -->
</table>
```

### 5. Verify with AI Review

Use `call_openrouter_model` with Gemini 2.5 Flash to review the document structure:

```python
call_openrouter_model(
    model='google/gemini-2.5-flash',
    prompt='Review this gift deed structure for completeness...\n[describe structure]',
    user_trigger_phrase='use openrouter gemini to review gift deed'
)
```

Ask it to check:
- Missing standard clauses (Registration Act, jurisdiction, severability)
- Whether the Schedule format is standard practice
- Any gaps in recitals or operative clauses

### 6. Folder & Sharing

- Create folder: `Personal > Gift Deed`
- Store document there, owned by ndr@draas.com
- Document naming: `YYYYMMDD_Deed_of_Gift_Donor_to_Donee`

## Source Documents Checklist

| Document | What It Contains | Where to Find |
|----------|-----------------|---------------|
| SHA (2020) v4/Final | Pre- and post-transfer shareholding per company | `Final Docs JUN2020/` or `Family/` |
| Deed of Gift (2020) | Individual gifts like Mantri Techzone Dharmesh→Nishant | `Family/` or `Family Settlement - Final - 2025/` |
| Family Arrangement Deed (2025) | Updated allocations, Mamata→NDR transfers, DR estate devolution | `Family Settlement - Final - 2025/` |
| Shareholding summary sheet | Comprehensive view per individual | `DR DDR Fmly Signed Docs/` — "DRA - Updated Shareholding..." |

## Pitfalls

- **Supersession rules**: The 2025 Deed says 2020 documents prevail UNLESS carved out in Clause 3.2. Verify each company's allocation source.
- **Scanned PDFs**: Family Settlement Deeds are often Adobe Scan exports (scanned images). Use pdftoppm + tesseract for OCR; expect imperfect character recognition.
- **Unsettled estate matters**: Some shareholdings (e.g., Eastern Farmlands, Quantum Services) are listed as "Unsettled DR Estate Matter" — the donor may not yet hold these shares in their own name.
- **Share transmission timing**: Allocations agreed in the Family Settlement may not have been transmitted to the donor's name by the gift deed date. Verify current share certificates.
- **Roshni's name**: User prefers "Roshni Ranka" (with one 'i' — Roshni, not Roshini).
