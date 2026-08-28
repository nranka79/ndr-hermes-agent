# Template-Based Google Docs: .docx → Drive Upload

**When:** You need to create or restructure a Google Doc with **complex table layouts** (multiple tables, row spans, specific table structures matching a source .docx template) and fill them with project-specific data.

This approach bridges the gap between two incomplete alternatives:

| Approach | Good for | Bad for |
|----------|----------|---------|
| **HTML import** (`google-doc-formatting-template` main method) | Visually rich docs from scratch, colored headers, callout boxes | Preserving exact source document table structure; editing an existing document |
| **Docs API batchUpdate** | Surgical text edits on existing docs, `replaceAllText` | Creating or restructuring tables — no table-create API; fragile cell edits |
| **python-docx → Drive Upload** (this method) | Populating a pre-designed .docx template with data, matching bank/SBI forms, legal formats | Rich visual formatting (colors, borders, callouts) — prefer HTML import for that |

## Workflow

### Step 1 — Download the .docx template from Drive

```python
from googleapiclient.http import MediaIoBaseDownload
import io

request = drive_service.files().get_media(fileId=TEMPLATE_DOC_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()
fh.seek(0)

from docx import Document
doc = Document(fh)
```

### Step 2 — Fill table cells with python-docx

```python
# Tables are accessed by index (0-based, in document order)
table = doc.tables[0]
table.rows[1].cells[2].text = "Entity Name"  # Specific cell by row/col
table.rows[2].cells[2].text = "PAN12345H"

# Filling multiple partner rows
for i, partner_data in enumerate(partners):
    row = table.rows[i + 1]  # skip header row
    row.cells[0].text = str(i + 1)
    row.cells[1].text = partner_data['name']
    row.cells[2].text = partner_data.get('age', '--')
```

### Step 3 — Upload as Google Doc (via Drive API import)

```python
output = io.BytesIO()
doc.save(output)
output.seek(0)

from googleapiclient.http import MediaIoBaseUpload

media = MediaIoBaseUpload(
    output,
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)

uploaded = drive_service.files().create(
    body={
        'name': 'Project Name - Builder Profile',
        'parents': [FOLDER_ID],
        'mimeType': 'application/vnd.google-apps.document'  # KEY: converts to Google Doc
    },
    media_body=media
).execute()
doc_id = uploaded['id']
```

### Step 4 — Apply remaining text fixups via Docs API

Some text may not survive the .docx→Google Doc conversion cleanly. Apply targeted `replaceAllText` fixes:

```python
docs_service.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'replaceAllText': {
            'containsText': {'text': 'old text', 'matchCase': True},
            'replaceText': 'new text'
        }
    }]}
).execute()
```

## ⚠️ Critical Pitfalls (from hard experience)

### 1. `replaceAllText` with SHORT NUMERIC STRINGS is dangerous

**NEVER use `replaceAllText` to replace a short number like `"20"` — it matches inside EVERY number that contains it:**

- `"20"` → `"130"` replaces inside `"12000"` → `"113000"` ❌
- `"20"` → `"130"` replaces inside `"2021"` → `"13021"` ❌
- `"20"` → `"130"` replaces inside `"201A"` → `"1301A"` ❌

**Safe approach — placeholder strategy:**

```python
# 1. Replace all known patterns containing "20" with placeholders
replace("2021", "YY21")
replace("202BA", "XXBA")
replace("over 20 years", "over TWENTY years")

# 2. Now replace remaining "20"s safely (only target cells remain)
replace("20", "130")

# 3. Restore placeholders
replace("YY21", "2021")
replace("XXBA", "202BA")
replace("over TWENTY years", "over 20 years")
```

### 2. `deleteContentRange` CANNOT delete the last content in a table cell

Google Docs API prevents deleting all content from a table cell — the cell must always retain at least one character:

```
Invalid deletion range. Cannot delete the requested range.
```

**Don't try `insertText` + `deleteContentRange` on the same range** — the insert shifts indices forward, so the delete range targets wrong content.

**Workaround**: Use the .docx approach (python-docx fills cells natively) or use `replaceAllText` with the placeholder strategy above.

### 3. Google Docs API write quota: 60 requests/minute/user

Each `batchUpdate` call counts as **one request** regardless of how many operations it contains. **Batch aggressively:**

```python
# GOOD: 30 replacements in one API call
docs_service.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': all_30_replace_requests}
).execute()

# BAD: 30 separate API calls — hits quota in seconds
```

Actual quota error:
```
Quota exceeded for quota metric 'Quota group for write operations'
and limit 'WriteRequestsPerMinutePerUser'
```

### 4. Table cell text has no newlines between paragraphs

When reading a table cell's content via the Docs API, each paragraph within the cell is a separate element. There are **no literal `\n` characters** between paragraphs. So `replaceAllText` with multi-line patterns like `"Total\n20\n12000"` will NOT match.

**Fix**: Do individual `replaceAllText` calls per cell value. The python-docx approach avoids this entirely since you set `.text` directly on cells.

## When to use this approach

- You have a **pre-designed .docx template** (bank letterheads, SBI forms, builder profile formats)
- The template has **6+ structured tables** that would be impractical to recreate via Docs API or HTML
- Data comes from a structured source (Google Sheets, project database, existing documents)

## Prerequisites

```bash
pip install python-docx  # or: uv pip install python-docx
```

Already available in the Hermes venv.

## Proven in production

This method was validated creating 3 SBI Builder Profiles (7 tables each) for Ranka Amber/Oasis/Udaya. The direct Google Docs API approach failed repeatedly due to table cell edit restrictions, short-number search contamination, rate limit issues, and multi-line replacement failures. The .docx approach succeeded in one clean pass per document.
