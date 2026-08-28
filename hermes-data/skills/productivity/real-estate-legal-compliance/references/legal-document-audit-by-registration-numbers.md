# Legal Document Audit by Registration Numbers

**Trigger:** A team member (Prakash, Nishant, etc.) sends a numbered list of 5–15 legal documents identified by registration number and/or description (e.g. "Will registered as 46/1981-82", "Rectification deed 1088/2014-15", "Conversion Order ALN(NAY)SR/60/2016-17") and asks you to check which are available on Drive.

This is distinct from:
- `court-order-drive-discovery.md` — finding ONE unknown document by legal provision name
- `bank-approval-document-audit.md` — audit against a bank's project financing checklist
- `buyer-legal-due-diligence-checklist-processing.md` — processing a buyer's lawyer's requisition

This workflow is for **auditing a structured, numbered list** of documents known by their registered document numbers.

## Workflow

### Phase 1: Account Resolution

1. Call `gws_resolve_account()` (no args) to list every known account and auth status in one shot
2. If only `google-draas` has tokens, search there first (it's the DRAAS shared business account)
3. Other accounts (google-ahfl, google-gmail) may not be authorised for Prakash — note this as a limitation

### Phase 2: Multi-Pass Search Per Document

For each document, run these search passes in order — do NOT stop after the first pass:

**Pass A — Full-text search for the exact registration number:**
```python
q = f"fullText contains '{reg_number}' or fullText contains '{reg_number_without_slashes}'"
```

**Pass B — Search for the document type + village/project:**
```python
q = f"name contains '{doc_type}' and name contains '{village}'"
```

**Pass C — Search for a broader keyword:**
```python
q = f"fullText contains '{keyword}'"
```

### Phase 3: Cross-Reference Structured Spreadsheets

Many DRAAS projects have **Legal Docs Verified spreadsheets** that are the definitive document inventory. These have multiple sheets:

| Sheet Name | Content | 
|-----------|---------|
| `Avail in Anupshah opinion` | Most comprehensive — lists every document by Sl No, Doc Type, Doc No, Date, Pages, Status, File No |
| `Allalsandra Index inc MDR & Anup Doc's` | Index of all documents with BBMP/MDR references, broken down by file category |
| `Noc Docs verified` | NOC documents with date/type verification |

**To read these sheets** (they are native Google Sheets, so Sheets API works):

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4', service_name='google-draas')
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'Avail in Anupshah opinion'!A:Z"
).execute()
```

**For .xlsx files** (like "Index of Documents.xlsx") — Sheets API returns `"This operation is not supported for this document"`. Download via Drive media API and parse the internal XML:

```python
from googleapiclient.http import MediaIoBaseDownload
import io, zipfile, html, xml.etree.ElementTree as ET

request = drive.files().get_media(fileId=FILE_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    _, done = downloader.next_chunk()
fh.seek(0)

with zipfile.ZipFile(fh) as zf:
    sheet_xml = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
    root = ET.fromstring(sheet_xml)
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    for row in root.findall('.//s:row', ns):
        for c in row.findall('s:c', ns):
            t = c.get('t', '')
            if t == 'inlineStr':
                is_elem = c.find('s:is', ns)
                if is_elem is not None:
                    t_elem = is_elem.find('s:t', ns)
                    val = html.unescape(t_elem.text or '') if t_elem is not None else ''
```

Note: .xlsx from Drive often uses `inlineStr` format (no separate shared strings file).

### Phase 4: Check Title Due Diligence Reports

The **Anup Shah Title Due Diligence Report** (available as a 3.5MB PDF per project) typically lists and references most registered documents. It won't contain the actual scanned copies, but it documents each document's existence, number, date, and parties.

Search for the registration numbers inside this report by:
1. Downloading the PDF
2. Using pdftotext for text-based pages, or pdftoppm + vision_analyze for scanned pages
3. Searching for the specific document number

### Phase 5: Classify Each Item

Classify into these buckets:

| Status | Meaning |
|--------|---------|
| ✅ **Indexed (Certified Copy / Original)** | Listed in the Legal Docs spreadsheet as available. The physical document exists with DRA's legal team but may not have a standalone scanned PDF in Drive |
| ✅ **Scanned PDF on Drive** | A separate PDF file found by that document number/name exists in Drive |
| ⚠️ **Partial** | Only some years/periods found (e.g. RTC 2018-19 found but not 2019-20 to 2025-26) |
| ⚠️ **Close match** | Similar document number found (e.g. HOA(S)85 instead of HOA 83) — verify if it's the same |
| ❌ **Not found** | No trace in any index or Drive search |

## Known Data Sources for Allalsandra / Ranka NorthStar (Sy No. 14/1)

| Source | Type | ID | Content |
|--------|------|----|---------|
| Legal Docs Verified | Google Sheet | `1mmTJJiBTaLUdKXte9j-VnRuSu1uL8YchjV3M8ZP_u3M` | 3 sheets: Balance Docs, Noc Docs Verified, Allalsandra Index inc MDR & Anup Doc's, Avail in Anupshah opinion |
| Index of Documents | .xlsx | `1CHYQj66_rxBvy9GTCx0tU5WHfI2z8rnQ` | 18 indexed documents (JDA, GPA, POA, Tax Receipts, Legal Opinions, Partnership docs, GST/PAN) |
| Title Due Diligence Report | PDF | `1LiHoho4Zxy4kxIpTf0_DbaOokagiIL8x` | Anup Shah's comprehensive report referencing all title documents |
| Banking Documents Folder | Drive Folder | `1IQ-8r3gxAfYOGAYxFF3qUqJnhfVRI1w7` | 19 key legal docs (JDA, GPA, POA, Tax receipts, Legal Opinions, Partnership docs) |
| Yelahanka Project Folder | Drive Folder | `1dSr0dLBeHqALTPlcN9lEMUFisTEbee2g` | Legal documents + DRA Ranka Holdings subfolders |

## Common Pitfalls

### 1. .xlsx files can't be read via Sheets API
Always check the Google Sheet metadata first — if the response says "This operation is not supported for this document. The document must not be an Office file," you're dealing with an .xlsx. Use media download + zip XML parsing instead.

### 2. EC is called "Search Report", not "Encumbrance Certificate"
In Karnataka revenue records, "Encumbrance Certificate" is officially called a **Search Report** or ಶೋಧ ವರದಿ (Shodha Varadi). The registration number format is `27120/2019-20`. Don't look for "EC" — look for "Search report" with the SRO registration number.

### 3. "Sharing Agreement" = "JDA" or "Joint Development Agreement"
The document Prakash calls "Sharing Agreement" between landowners and developer is indexed as "Joint Development Agreement" (document no. 3033/2013-14, 28 pages). These are the same thing — the revenue-share terms between LO and developer are embedded in the JDA.

### 4. Death certificates and Wills may only exist as index entries
These are often listed in the Legal Docs sheet as "Photocopy" with a file number but no entry in the "Document Link" column. They're physical documents held by the legal team, not scanned PDFs on Drive. Report them as "✅ Indexed (physical copy)" rather than "❌ Not found".

### 5. Registration numbers may only appear inside index sheets, not filenames
A document like "Rectification deed 1088/2014-15" may not have a PDF named `1088-2014-15.pdf`. Instead, it's listed in the "Avail in Anupshah opinion" sheet as a row entry. The index sheet IS the authoritative record of what exists.

### 6. gnuts_skill_bridge raw_query bug
`gws_skill_bridge.call("drive_search", query=..., raw_query=True)` raises `AttributeError: 'SimpleNamespace' object has no attribute 'raw_query'`. Workaround: write a script to disk and run via `terminal()` using `gws_auth.build_service()` directly.

### 7. execute_code sandbox can't reach the vault
The execute_code sandbox lacks the `GWS_VAULT_SOCKET` environment variable. Always write scripts to `/tmp/` and run via `terminal()` with `workdir=/opt/hermes`. Pattern:
```python
# In execute_code:
from hermes_tools import write_file, terminal
write_file("/tmp/script.py", content)
result = terminal(f"python3 /tmp/script.py", timeout=60)
```

### 8. "RTC for 2018-19 to 2025-26" may be a multi-year request
RTCs are often bundled as multi-year sets (2001-02 to 2017-18, etc.) rather than every single year. Check the Legal Docs sheet for each year separately. A request for 2018-19 to 2025-26 may have gaps.

### 9. FileLink vs Link Column in Index sheets
When querying "Avail in Anupshah opinion", the last column has a Drive link only for some entries. Documents marked "NO" in the "ANUP SHAH (AVAIL STATUS)" column don't have links — these were not part of the title report's verified set. The legal team holds physical copies separately.

## Example Classification Report Format

```
## Document Availability Report

**11. RTC for 2018-19 to 2025-26 — Sy. No. 14/1**
⚠️ Partial
- ✅ 2024-2025 RTC sy no 14_1.pdf found
- ✅ RTC 2018-19 indexed as "photocopy"
- ✅ RTC 2001-02 to 2017-18 (certified copy) available
- ❌ RTCs 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2025-26 not found

**12. Re-grant order — HOA No. 83/1968-69**
⚠️ Close match — "Report by Tahsildar, HOA(S)85/1968-69" found (number differs by 2)
- Verify if the same document. Referenced in Anup Shah Title Report.

**13. Will — Document No. 46/1981-82**
✅ Indexed as "Will (Hanumaiah), 46/1981-82, 3 pgs, Certified Copy"
```
