# Document Retrieval + Multi-Source Analysis

**Trigger:** User asks you to find a document (agreement, contract, SSA, area statement, etc.) and analyze its contents — extract tables, identify missing columns, cross-reference against other documents or spreadsheets.

This extends the basic email-document-retrieval workflow (which covers "find a PDF in email") to multi-source, multi-format document analysis where you need to correlate data across documents.

## Workflow — 6 Phases

### Phase 1: Source Identification

Parse the user's request for:
- **Document type** — SSA, JDA, Area Statement, Sanction Plan, Certificate
- **Project name** — Ranka Amber, Ranka Udaya, etc.
- **Recipient** who it was sent to — Raghu Iyer, Prakash, etc.
- **Sender** — Nishant, lawyer, government body
- **Keywords** — "supplementary sharing agreement", "area statement"
- **Date range** — "latest", "April 2026", "final draft"

### Phase 2: Gmail Search — Find the Email with Attachments

Search Gmail with multiple query strategies, escalating scope:

```python
# Strategy 1: Narrow — specific document name + recipient
q = 'Ranka Amber supplementary sharing agreement Raghu Iyer OR rmiyer@bitanz.com'

# Strategy 2: Broader — project + doc type
q = 'Ranka Amber SSA OR "Supplementary Sharing Agreement"'

# Strategy 3: Wildest — project + person
q = 'Raghu Iyer OR rmiyer@bitanz.com ranka amber'
```

**Key technique — check the reply chain too:**
- The original SSA email from Nishant may have been sent as `.docx` attachment
- The reply from the landowner (Raghu) may reference the same document
- Both sides of the conversation give context

### Phase 3: Download Attachments

Once the right email is found, download ALL attachments — not just the main document:

```python
# Identify attachments by filename and mimeType
for part in parts:
    fn = part.get('filename', '')
    mime = part.get('mimeType', '')
    if fn and 'attachmentId' in part.get('body', {}):
        # Download: SSA.docx, Area_Statement.xlsx, Parking_Plan.pdf, Sanction_Plan.pdf
        att = service.users().messages().attachments().get(
            userId='me', messageId=msg_id, id=part['body']['attachmentId']
        ).execute()
        file_data = base64.urlsafe_b64decode(att['data'])
```

**Save to `/opt/data/`** for persistence across analysis steps.

### Phase 4: Document Analysis — Extract Content by Type

| Format | Tool | What to Extract |
|--------|------|----------------|
| **.docx** | `python-docx` (`Document`) | Tables (`doc.tables`), paragraphs (`doc.paragraphs`), section headings |
| **.xlsx** | `openpyxl` | Sheets, column headers, row data, formulas |
| **Application/vnd.google-apps.spreadsheet** | Google Sheets API | Same as xlsx — read via `service.spreadsheets().values().get()` |

**Docx table extraction pattern:**
```python
from docx import Document
doc = Document('path.docx')
for ti, table in enumerate(doc.tables):
    print(f"Table {ti}: {len(table.rows)} rows x {len(table.columns)} cols")
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        # Identify: column headers, data rows, allocation tables
```

**Xlsx analysis pattern:**
```python
from openpyxl import load_workbook
wb = load_workbook('path.xlsx')
for sname in wb.sheetnames:
    ws = wb[sname]
    # Read headers from first row
    headers = [cell.value for cell in ws[1]]
    # Then iterate data rows
```

### Phase 5: Google Drive Search — Find Related Sheets

After finding the email attachment, also search Google Drive for related live/collaborative versions:

```python
# Search for project-specific sheets
results = drive.files().list(
    q="name contains 'Amber' and name contains 'statement' and mimeType='application/vnd.google-apps.spreadsheet'",
    fields='files(id, name, webViewLink, modifiedTime)'
).execute()
```

**Typical related sheets found:**
- "Amber - Area Statement (lattest April 2026)" — live collaborative version of the emailed xlsx
- "Ranka Amber - Sanction Plan Area Statement April 2026" — alternative version
- "Area Statement - Ranka Amber (April 2026)" — earlier/different snapshot
- "Amber Area Statement old" — historical

### Phase 6: Cross-Reference & Gap Analysis

Compare what's in the SSA schedules vs what's in the area statement sheet:

**1. Map the SSA tables to their schedules:**
- Schedule B table(s) — usually the master inventory (all 20 units)
- Landowner allotment table — units assigned to LO
- Developer allotment table — units assigned to DEV
- Parking allocation table
- Property description table

**2. Compare columns across documents:**

| Column | SSA Schedule B | Area Statement Sheet | Notes |
|--------|---------------|---------------------|-------|
| Unit No. | ✅ | ✅ | Match |
| Floor | ✅ | ✅ | Match |
| Plan Unit No. | ✅ | ❌ | Only in SSA |
| Built-up Area (sq.ft) | ❌ (noted: same as carpet) | ✅ | Gap in SSA |
| Carpet Area (sq.m) | ✅ | ✅ | Match |
| Carpet Area (sq.ft) | ❌ | ✅ | Gap in SSA |
| Super Built-up Area (sq.ft) | ✅ | ✅ | Match |
| UDS (Undivided Share) | ❌ | ❌ | **Missing from both** |

**3. Report the gap clearly:**
- List all columns present in each document
- Identify the specific missing column(s)
- Explain what the missing column represents and how it's calculated
- Offer to update the SSA, the sheet, or both

**4. UDS calculation formula (from Jun 2026 session for Ranka Amber):**
```
UDS = Unit SBUA × (Total Plot Area / Total SBUA)
     = Unit SBUA × (14,000 / ~31,853)
     = Unit SBUA × 0.4395 sqft per sqft of SBUA
```

## Real Worked Example — Ranka Amber SSA + Area Statement (Jun 2026)

**Request:** "Find the SSA I shared with Raghu Iyer, find all schedules with tables, and cross-reference against the Amber area statement sheets to identify what's missing."

**Source identification:**
- Document: Supplementary Sharing Agreement (SSA) for Ranka Amber
- Recipient: Raghu Iyer (rmiyer@bitanz.com)
- Also: Manohar Singh CC'ed
- Approximate date: May/June 2026 (recent)

**Gmail search identified:**
- Email: "Ranka Amber – Supplementary Sharing Agreement (Final Draft) for Review and Execution" — 3 Jun 2026
- Reply: Raghu's review on 8 Jun 2026

**Attachments found (4):**
1. `SSA_Ranka_Amber_FINAL_v3.docx` (19.8 KB) — the agreement
2. `Area_Statement_Ranka_Amber_April_2026.xlsx` (34.6 KB) — area breakdown
3. `Ranka_Amber_Stilt_Floor_Parking_Sharing_Plan.pdf` — parking plan
4. `Ranka_Amber_Sanction_Plan_07.05.2026.pdf` — BBMP sanctioned plan

**SSA tables extracted (7 total):**
- Table 0: Ground floor (101-105) + Third floor (401-405) — Carpet Area sq.m, SBUA sq.ft
- Table 1: First floor (201-205) + Second floor (301-305) — same column set
- Table 2: Parking allocation (21 slots: 10 LO, 10 DEV, 1 visitor)
- Table 3: Property description (Survey 4/124, PID 7057785976, 14,000 sqft)
- Table 4: Master inventory — all 20 units with Floor, Plan Unit, Market No, Carpet Area sq.m, SBUA sq.ft, Allotted To (LO/DEV)
- Table 5: Parking (duplicate of Table 2)
- Table 6: Sanction reference (LP No., RERA status)

**Area Statement Sheet columns:**
`# | Marketing Unit # | SHARE (LO/DEV) | Configuration | Sanction Floor | Entrance Facing | No.of Toilets | Built-up Area(sft) | % against builtup Area | Balcony Area(SQFT) | Carpet Area(SQFT) | Carpet+Balcony(SQFT) | FAR Common Area Share(SQFT) | Super Built Up Area(SQFT) | RERA Carpet Area(sqft) | Vastu Score | Area in Sqm | Sanction Carpet Area(sqm)`

**Gap identified:** Both the SSA schedules AND the area statement sheet were missing an **UDS (Undivided Share of Land)** column. This column is critical for:
- Defining each apartment owner's proportionate ownership in the total land
- RERA compliance — every sale deed must specify UDS
- Future unit sales — buyers need this number for their title documents

## Why This Pattern Matters

Multi-source document analysis occurs whenever:
- A project has multiple agreement versions (SSA, JDA, addendum) that need reconciliation
- Area data exists in both a legal agreement (SSA) and an architect's spreadsheet
- A user says "we have the data in the sheet but need it reflected in the agreement too"
- Before executing legal documents, you need to verify all data points are complete

One search-email → download → analyze → cross-reference pipeline replaces 4-5 separate tool calls with no analysis context.
