# Project Finance Dataroom Spreadsheet

When the user needs a comprehensive **Company Profile + Required Docs Checklist + Project-Wise Document Inventory** spreadsheet for a project finance / loan application — one sheet combining firm/entity KYC, promoter profiles, financial data, required-document-checklist, and per-project document tables with Drive links.

This is **not** a per-survey deed index (`folder-index-spreadsheet.md`) or a per-project categorized checklist (`project-checklist-categories.md`). It is a **bank/project-finance dataroom** — a single sheet that tells a lender everything they need: who the group is, who the promoters are, which documents are available, and where each project document lives on Drive.

## Structure

A project-finance dataroom typically has 8 sections in one sheet:

| Section | Content |
|---------|---------|
| 1. About DRA Group | Group name, experience, presence, founder, leadership, JV partners |
| 2. Promoter Profile | Education, experience, PAN/Aadhaar/Address, real estate + tech ventures |
| 3. KYC — Directors & Partners | Table per person: PAN, Aadhaar, role, doc links |
| 4. KYC — Entity Documents | Table per firm/company: PAN, GST, CIN/Regn No, Address, all doc links |
| 5. Required Documents Checklist | #, Required document, Status (✓/⚠/Pending), Drive link(s) |
| 6. Project-Wise Documents | One table per project: doc type, description, drive link |
| 7. Enterprise Data Links | Links to external Enterprise Data and Portfolio sheets |
| 8. Project Summary Table | Projects x (type, units, land area, location, RERA status, entity) |

## Key Technique: Multi-HYPERLINK with `& CHAR(10) &`

A single cell cannot contain two independent `=HYPERLINK(...)` formulas separated by commas — concatenating them as `=HYPERLINK(u1,"t1"), =HYPERLINK(u2,"t2")` produces `#ERROR!` because Sheets interprets the comma as a formula separator, not text.

**Fix:** concatenate formulas with `& CHAR(10) &`:

```python
def link_multi(*items):
    """Build multiple HYPERLINK formulas stacked with CHAR(10) for display"""
    formulas = []
    for text, url in items:
        if url and text:
            escaped_url = url.replace('"', '""')
            escaped_text = text.replace('"', '""')
            formulas.append(f'HYPERLINK("{escaped_url}","{escaped_text}")')
    if not formulas:
        return ''
    if len(formulas) == 1:
        return f'={formulas[0]}'
    joined = ' & CHAR(10) & '.join(formulas)
    return f'={joined}'
```

Usage:
```python
rows.append(['3', 'KYC docs', '✓ Available', link_multi(
    ('NDR PAN+Aadhaar', get_web_link('1BevTvsSBI13xkeTkCCa')),
    ('Kishan PAN+Aadhaar', get_web_link('1WRxjrojhcu8u1TUGDRG'))
)])
```

Write with `valueInputOption='USER_ENTERED'` so Sheets evaluates the formulas.

## Helper: `get_web_link()`

To get a shareable Drive link from a file ID, always escape parentheses in the URL (HYPERLINK formula breaks on unescaped `(` and `)`):

```python
def get_web_link(file_id):
    try:
        meta = drive.files().get(fileId=file_id, fields='webViewLink').execute()
        url = meta.get('webViewLink', '')
        url = url.replace('(', '%28').replace(')', '%29')
        return url
    except:
        return f'https://drive.google.com/file/d/{file_id}/view'
```

## Helper: Token Access Pattern

When running a GWS script that builds this spreadsheet, use `gws_fetch_token` to get the token JSON inline rather than reading from the vault path directly (the vault path may not exist in the expected location):

```python
# Get token via gws_fetch_token tool (not from filesystem)
# In the script, embed the token JSON as a string literal

tok = json.loads('''{"token": "...", "refresh_token": "...", ...}''')
creds = Credentials.from_authorized_user_info(tok, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
sheets = build('sheets', 'v4', credentials=creds)
drive = build('drive', 'v3', credentials=creds)
```

## Helper: Project Section Builder

Build structured document inventory tables per project with consistent columns:

```python
def add_project_section(rows, project_name, rera_no, docs):
    """docs is a list of tuples: (doc_type, description, link_or_text)
       or 4-tuples: (doc_type, description, link_text, url)"""
    rows.append([project_name])
    rows.append(['Document Type', 'Description', 'Drive Link'])
    for doc in docs:
        if len(doc) == 4:
            doc_type, desc, link_text, url = doc
            if url:
                rows.append([doc_type, desc, link_text if url.startswith('http') else link(link_text, url)])
            else:
                rows.append([doc_type, desc, link_text])
        else:
            doc_type, desc, link_text = doc
            rows.append([doc_type, desc, link_text])
    rows.append([])
    rows.append(['RERA No', rera_no])
    rows.append([])
```

## Token Identity Pitfall

- **Always use `gws_resolve_account()` first** to confirm which token is available.
- **Auth email can flip mid-session.** Load `creds`, THEN verify identity: `svc.about().get(fields='user').execute()['user']['emailAddress']`.
- If the script needs to read Drive folders shared to a specific user (e.g. psingh), prefix with `HERMES_SESSION_USER_ID=<slug>` OR embed the token inline after fetching it via `gws_fetch_token` — do NOT rely on the session default mapping.

## Drive Folder Discovery

Before building the dataroom, always walk the actual Drive folders:

1. **Find project folders** by name: search `name contains 'RANKA AMBER' and mimeType='application/vnd.google-apps.folder'`
2. **Disambiguate** — multiple folders may share a name; distinguish by ID. The canonical project folders often live under a parent "Master data" folder (`1I4Xg61gV8khNHCPfOmiNReqmRjt4EJEg`).
3. **Recursively list contents** (2 levels deep) to find brochures, plans, legal docs, RERA certs, area statements.
4. **Build `get_web_link()` references** for each key doc to embed as HYPERLINK.

Typical per-project docs to look for:
- Brochure / marketing deck / renders
- Approved Plan / Sanction letter / Building Licence
- RERA certificate / RERA order
- Architect Certificate / Area Statement
- EC (Encumbrance Certificate)
- E-Khata / BBMP Tax receipts
- JDA / GPA / Addendum / Development Agreement
- Sale Deeds / Title Documents
- Legal Opinions / Title Reports
- Partnership deeds (firm-level)
- Gift Deeds / Relinquishment Deeds
- NOCs (KSPCB, BWSSB, BESCOM, etc.)
- Project documents folder link
- Enterprise data / portfolio spreadsheet links

## Example: Required Docs Checklist for Project Finance

| # | Required Document | Status | Link |
|---|-------------------|--------|------|
| 1 | Brief Profile of the Group | ✓ Available | (included in sheet) |
| 2 | Profile of Promoters | ✓ Available | (included in sheet) |
| 3 | KYC of Directors | ✓ Available | =HYPERLINK(...) & CHAR(10) & HYPERLINK(...) |
| 4 | KYC of Entity (PAN/GST/COI/MOA/AOA) | ✓ Available | =HYPERLINK(...) & CHAR(10) & HYPERLINK(...) |
| 5 | Enterprise Data Sheet | ✓ Available | =HYPERLINK(...) |
| 6 | Net Worth Certificate | ⚠ Check required | NDR ITR: =HYPERLINK(...) |
| 7 | Last 3 Years Financials | ⚠ Partial | Refer to entity sheets |
| 8 | Sanction Letter & SOA of Existing Loans | ⚠ Pending | — |

## Pitfalls

- **`=` vs plain text:** Every HYPERLINK formula MUST start with `=`. Without it, Sheets writes the formula text literally. When using `valueInputOption='USER_ENTERED'`, a string starting with `=HYPERLINK(...)` is evaluated as a formula; any other value is plain text.
- **Commas inside HYPERLINK arguments:** Single HYPERLINK formulas work fine with commas (`=HYPERLINK("url","text")`). The problem is concatenating *multiple independent* HYPERLINK formulas in one cell — use `link_multi()` with `& CHAR(10) &`.
- **`CHAR(10)` only works with `USER_ENTERED`** — if using `RAW`, the formula text including `CHAR(10)` is treated as literal text. Always use `valueInputOption='USER_ENTERED'`.
- **Parentheses in Drive URLs** — Google Drive file links can contain `(` and `)` in filenames. These must be escaped to `%28` and `%29` before embedding in a HYPERLINK formula, or Sheets errors on the formula.
- **`addSheet` doesn't return sheetId reliably** — after creating sheets, fetch `spreadsheets().get(fields='sheets.properties')` to map title → sheetId.
- **STALE MERGES:** If rewriting an already-formatted sheet, prefer `drive.files().create` (new file) rather than `values().clear()` + rewrite — cleared merges persist and swallow values.
- **`add_project_section` tuple shape:** Some tuples are 3-element (no separate URL — the link_text IS a HYPERLINK formula) and some are 4-element (link_text + url separate). The helper must handle both.