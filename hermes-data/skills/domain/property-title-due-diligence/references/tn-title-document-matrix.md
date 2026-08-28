# Tamil Nadu Title Document Matrix Workflow

## When to use
User provides a Title Scrutiny Report (TSR/legal opinion PDF) for a Tamil Nadu land aggregation + a Google Drive folder of scanned legal documents. They want survey-wise folders and a structured document matrix.

## Workflow

### 1. Extract TSR Data
- Use `pdftotext -layout <input.pdf> <output.txt>` to extract full text from the legal opinion PDF
- Read the PDF in sections (it's typically 2000+ lines)
- Key sections to extract:
  - **Part I**: Documents Furnished (numbered list of deeds, Pattas, ECs, certificates)
  - **Part III**: Schedule of Property (survey numbers with boundaries)
  - **Part V**: Flow on Title (each survey's chain of title from origin to current)
  - **Part VI**: Observations & Suggestions (final ownership table + missing documents + subject-to conditions)
- Ownership table in Part VI gives definitive list: 34 survey numbers, each with extent, owner, Patta number

### 2. Build Survey Metadata
For each survey number, capture:
- Survey number (e.g. 158/1C3)
- Extent in Acres
- Current owner name
- Patta number
- Title chain summary (who conveyed to whom)

### 3. Scan Google Drive
- Use `gws_resolve_account` to get the user's Google service name
- `build_service('drive', 'v3', service_name=...)` to access Drive
- List ALL files recursively (parent folder + subfolders)
- Check folder permissions early: `files().get(fileId=..., fields='capabilities,owners')` - if `canAddChildren: false`, you can't create subfolders

### 4. Match Documents to Surveys
TN naming conventions vary widely. Build comprehensive matching:

```
Patta 158(1C3).pdf          → 158/1C3
SyNo. 158-1C9B.pdf          → 158/1C9B  
sy.no.166_3F.pdf            → 166/3F
Syno-158-1A1A.pdf           → 158/1A1A
sale deed sy no 158/1B.pdf  → 158/1B2 etc.
158 1A1A.pdf                → 158/1A1A (Pattas FMBs folder)
1663A.pdf                   → 166/3A (compact, no separator)
```

Key variant patterns to check:
- `{base}{sub}` (compact: 1663A)
- `{base}({sub})` (parenthesis: 158(1C3))
- `{base} {sub}` (space: 158 1A1A)
- `{base}-{sub}` (hyphen: 158-1C9B)
- `{base}_{sub}` (underscore: 158_1C9B)
- `{base}.{sub}` (dot: 158.1C9B)
- Prefix forms: `Patta`, `SyNo`, `sy.no`, `syno`, `Sy`, `no.`

### 5. Create Google Sheets Spreadsheet
- Create via `sheets.spreadsheets().create()` with 35 sheets (1 SUMMARY + 34 survey sheets)
- Sheet naming: replace `/` with `_` (e.g. `Sy_158_1C3`)
- Document categories per survey sheet:
  - Title Deed (current owner)
  - Chain of Title Deeds
  - Partition / Exchange / Gift / Settlement Deeds
  - Encumbrance Certificate (EC)
  - Patta / Chitta (current)
  - FMB / Sketch
  - UDR A-Register
  - Adangal & Tax Receipts
  - Village Map / Aggregation Sketch
  - Legal Opinion / Title Report
  - Death Certificates
  - Legal Heirship Certificates
  - GPA / SPA / POA
  - Agreements & Cancellation Deeds
  - Family Tree / Genealogy
  - Firm/Company Documents
  - Revenue Receipts (up-to-date)
- Mark missing docs with ⚠️
- Add TSR-specific missing documents per survey
- Add "Subject to" conditions from TSR Part VI (Adangal, original verification, public notice)

### 6. Drive Permissions Pitfall
- The parent folder may be owned by a different account (e.g. presales.blr@draas.com)
- The user's account (psingh@draas.com) may only have read access
- `canAddChildren: false` → cannot create subfolders
- Solution: ask the user to share edit/write access, or have the folder owner create folders

### 7. Multi-Survey Files
Many deeds cover multiple survey numbers (e.g. "Sale Deed No 21785/2024 for Sy NO 158-1C3,1C4,1C6,1C9A"). These need to be:
- Listed in each relevant survey's sheet
- Flagged as "combined deed" in remarks

## Common TSR Missing Documents (TN)
- Death & Legal Heirship Certificates of persons in the chain (Pappi Reddy, Munnusamy Reddy, Guvva Reddy etc.)
- UDR Pattadhars for joint patta holders
- Balance share ownership proof
- Specific GPA documents referenced in chain
- Up-to-date Adangal & Kist receipts
- Original document verification certificates