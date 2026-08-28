# Firm Dossier Compilation (Data-Extraction Variant)

A variant of `document-dossier-compilation` where the task is NOT to compile original PDFs into a bound dossier, but to **extract structured data** from scanned legal/financial documents across multiple Drive folders and **synthesize a new Word (.docx) dossier** with tables, summaries, and document inventories.

**Trigger phrases:** "make a word file for each firm", "generate dossier for [company/partnership]", "compile firm details with financials", "check my drive for [project] folders and extract firm documents"

## When to use this variant

| Aspect | Standard (PDF Compilation) | This Variant (Data-Extraction Dossier) |
|--------|---------------------------|----------------------------------------|
| Input | Many PDFs from one Drive folder | PDFs from MULTIPLE project folders across Drive |
| Output | One bound PDF per person/category | One Word (.docx) per entity with structured tables |
| Extraction | Classify & attach original PDFs | OCR & extract: dates, ratios, amounts, registration numbers |
| Synthesis | Title page + summary + timeline + originals | Firm details + financial tables + partner ratios + reconstitution history + document inventory with Drive links |

## Workflow

### Phase 1: Discover & Map

1. **Identify all entities** the user named (e.g. "DRA Realty Pvt Ltd, Seveganapalli Land Partners, DRA Thindlu Land Partners, DRA Ranka Holdings").
2. **Search the named project folders** (Oasis - Print, Ranka Amber, Ranka Udaya, Ranka Northstar, etc.) for firm-related subfolders:
   ```python
   svc = build_service('drive', 'v3', service_name='google-draas')
   # Broad search first
   resp = svc.files().list(q="name contains 'firm' and trashed=false",
      fields='files(id, name, webViewLink)').execute()
   # Then specific folder searches
   resp = svc.files().list(q="'PARENT_ID' in parents and trashed=false",
      fields='files(id, name, mimeType, webViewLink)').execute()
   ```
3. **Look for folder naming patterns:**
   - `"[Entity Name] - firm related documents"`
   - `"Firm Related Documents"` (generic — list contents to classify)
   - `"Financial Documents for [Entity]"`
   - `"[Entity]"` (direct match folder)

### Phase 2: Download Critical Documents

For each entity, download:
- Partnership deed / incorporation certificate (date, partners, ratio)
- Registration acknowledgement (Form C/10A — registration number + date)
- Any reconstitution deeds (addendums, change in partners)
- Reconciliation acknowledgements (Form D)
- ITR acknowledgements (last 3 years minimum)
- PAN / GST / TAN certificates
- Address change acknowledgements

**Download from Drive:**
```python
from googleapiclient.http import MediaIoBaseDownload
import io

request = svc.files().get_media(fileId=FILE_ID)
content = io.BytesIO()
downloader = MediaIoBaseDownload(content, request)
done = False
while not done:
    _, done = downloader.next_chunk()
with open(f'/tmp/firm_docs/{name}.pdf', 'wb') as f:
    f.write(content.getvalue())
```

### Phase 3: OCR & Extract Structured Data

**Check if text-based or scanned:**
```bash
pdftext /tmp/firm_docs/doc.pdf - | wc -c
```
- \> 50 chars → text-based, use `pymupdf`
- ≤ 50 chars → scanned, use `pdftoppm` + OCR

**For scanned documents:**
```bash
pdftppm -png -r 300 -f 1 -l 3 /tmp/firm_docs/doc.pdf /tmp/firm_imgs/doc
```
Then `vision_analyze` each page sequentially. Never parallelize pages of the same document — vision has no cross-page memory.

**Key data to extract per document type:**

| Document Type | Target Fields |
|---|---|
| **Partnership Deed** | Date of deed, all partners' full names, addresses, profit-sharing ratio/%, capital contributions, firm name, business object, financial year end, any special clauses |
| **Registration Ack (Form C/10A)** | Registration number (e.g. SJN-F490-2023-24), date of registration, firm name, registered address, registering office (Shivajinagar etc.) |
| **Reconstitution Deed** | Date, incoming/outgoing partners, date of joining/ceasing, new sharing ratio, reason for reconstitution |
| **Recon Ack (Form D)** | Final registration number, date of reconstitution, incoming partner details, outgoing partner details |
| **ITR Acknowledgement** | Assessment year, PAN, total income, business profit/loss, net tax payable, taxes paid, refund due |
| **General Financial Statement** | Total Income, Revenue, Net Profit/Loss, Total Assets, Share Capital, Reserves, Auditor |

### Phase 4: Cross-Reference & Compile

Before writing the dossier, verify consistency across documents:
- **Registration number** should be consistent across acknowledgement and all subsequent filings
- **Partners** should trace correctly: original deed → addendums → reconstitution → current state
- **Sharing ratio changes** should follow a clear chain from original to current
- **Dates** must be sequential: deed date ≤ registration date ≤ reconstitution dates

### Phase 5: Generate Word Dossier

Use `python-docx` (pre-installed in Hermes venv at `/opt/hermes/.venv/bin/python3`):

```python
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
# Section 1: Firm Details
doc.add_heading("FIRM DOSSIER", level=0)
doc.add_heading("Firm Name", level=1)

# Use add_bold_para pattern
def add_bold_para(doc, label, value=""):
    p = doc.add_paragraph()
    run = p.add_run(label + ": ")
    run.bold = True
    if value:
        p.add_run(value)

# Section 2: Registration & Deed Details
add_table(doc, ["Particular", "Detail"], [
    ["Date of Partnership Deed", "..."],
    ["Date of Registration", "..."],
    ["Registration Number", "..."],
])

# Section 3: Partner Structure with ratios
add_table(doc, ["Partner", "Profit Sharing %", "Capital Contribution", "Role"], [
    [...]
])

# Section 4: Financial Summary (table per year)
add_table(doc, ["Particulars", "FY 22-23", "FY 23-24", "FY 24-25"], [...])

# Section 5: Reconstitution History
# Section 6: Document Inventory (with Drive links)
# Section 7: Drive Folder Links
```

**Table helper:**
```python
def add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        hdr.cells[i].text = h
        for p in hdr.cells[i].paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)
    for row_data in rows:
        row = table.add_row()
        for i, val in enumerate(row_data):
            row.cells[i].text = str(val)
            for p in row.cells[i].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
    doc.add_paragraph()
```

### Phase 6: Document Inventory with Drive Links

After each document name, include the Drive link as a smaller-font sub-bullet pointing to the exact file:
```python
add_bullet(doc, "Partnership Deed (4 Aug 2023)")
p = doc.add_paragraph(style='List Bullet 2')
p.add_run(f"Link: {drive_link}").font.size = Pt(8)
```

## Entity-specific Extraction Notes

### Private Limited Company (e.g. DRA Realty Pvt Ltd)
- Date of Incorporation (from incorporation certificate)
- PAN / GST / CIN
- Director details
- **Financial data is most complete** — ITR-6 acknowledgements show 3-year trends
- MOA/AOA govern the entity

### Partnership Firm (e.g. Seveganapalli Land Partners, DRA Thindlu)
- Registration number pattern: `SJN-FXXX-YYYY-YY` (Office: Shivajinagar, Bangalore)
- Partnership deed date often differs from registration date by days/weeks
- Reconstitution deeds may NOT be explicitly labelled — look for "Retiring of [Name]" in the filename
- Profit sharing is typically **in proportion to capital contributions** (not fixed percentages)
- Check for: voting weighted by capital, majority partner controls banking, annual profit distribution date

### Multi-Stage Partnership (e.g. DRA Ranka Holdings)
- Trace full evolution: Original deed → Addendums → Reconstitutions
- Original partners may be different from current (death, retirement, admission of legal heirs)
- Each stage has its own sharing ratio and capital contributions
- Addendums often say "all other terms of original deed remain same"

## ITR Financial Data Extraction Notes

ITR-6 acknowledgements (used by companies) contain:
- **Total Income** — may differ significantly from accounting revenue
- **Business Loss** — shown separately, may reduce total income to 0
- **Taxes Paid** — includes TDS/TCS paid; often exceeds final liability
- **Refund Due** — when taxes paid > tax on total income
- **ITR-6 is a TAX document, not a full P&L** — balance sheet items (share capital, reserves, total assets) are NOT in the acknowledgement

For partnership firms, ITR-5 acknowledgements may be available separately.

## Pitfalls

- **ITR acknowledgement is NOT the full financial statement.** Balance Sheet and P&L detail pages (assets, liabilities, revenue breakdown) are often in separate PDFs or embedded pages within the same file that were auditor's certification pages, not the actual statements. When the user wants "all financial details", note what's available and flag what's missing.
- **Financial documents may live in separate folders** not nested under project folders. Search Drive broadly: `name contains 'Financial' and name contains '[Entity]'`.
- **Scanned ITR PDFs can be huge** (8-12MB each for 10 pages) — 3 years × 8MB = 24MB+ download. Batch sequentially.
- **For new firms** (registered < 1 year ago): expect zero ITR data. Note this in the dossier rather than leaving blank sections.
- **Vision_analyze pages sequentially** — do not send multiple pages of the same scanned document simultaneously, as each call has no memory of adjacent pages.
- **OCR totals are unreliable** — verify arithmetic: GST @ 18% should match net × 0.18. Cross-check before recording.
- **Drive link formatting**: Google Drive links from the API contain `&usp=drivesdk` parameters — keep them intact. They're valid permanent links.