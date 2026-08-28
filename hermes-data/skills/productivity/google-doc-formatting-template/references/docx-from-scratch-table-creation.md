# DOCX-from-Scratch: Creating Google Docs with Proper Tables

**When:** You need a structured Google Doc with **actual tables** (not text-based layouts) and you're starting from data, not a template. The DOCX bridge approach avoids:
- Google Docs API's lack of a `createTable` endpoint (only `insertTable` at fragile indices)
- HTML import's `<ol>/<li>` garbage numbering bug
- Repeated `batchUpdate` index-shifting problems

## Workflow Overview

1. Build a .docx with `python-docx` — tables, headers, data rows, styling
2. Upload to Drive with `mimeType='application/vnd.google-apps.document'` (auto-converts)
3. Make URLs clickable via Docs API `updateTextStyle` with `link`

---

## Step 1 — Build the .docx from scratch

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

# Set default font
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

# ─── Title ───
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('DOCUMENT TITLE')
run.bold = True
run.font.size = Pt(18)

# ─── Table with styled header ───
table = doc.add_table(rows=4, cols=3)
table.style = 'Light Shading Accent 1'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

# Set column widths
for row in table.rows:
    row.cells[0].width = Cm(1.5)
    row.cells[1].width = Cm(6)
    row.cells[2].width = Cm(10)

# Header row
headers = ['#', 'Name', 'Link']
for i, h in enumerate(headers):
    cell = table.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in paragraph.runs:
            run.bold = True

# Data rows
data = [
    ('1', 'Item One', 'https://docs.google.com/document/d/.../edit'),
    ('2', 'Item Two', 'https://docs.google.com/document/d/.../edit'),
    ('3', 'Item Three', 'https://docs.google.com/document/d/.../edit'),
]
for ri, (num, name, url) in enumerate(data, 1):
    table.rows[ri].cells[0].text = num
    table.rows[ri].cells[1].text = name
    table.rows[ri].cells[2].text = url
    for paragraph in table.rows[ri].cells[0].paragraphs:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Save
doc.save('/tmp/output.docx')
```

### Styling options that work

| Element | Code |
|---------|------|
| **Table style** | `table.style = 'Light Shading Accent 1'` (built-in) |
| **Bold text** | `run.bold = True` |
| **Font size** | `run.font.size = Pt(14)` |
| **Font color** | `run.font.color.rgb = RGBColor(0, 102, 204)` |
| **Center align** | `paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER` |
| **Bullet list** | `doc.add_paragraph('  • Item', style='List Bullet')` |
| **Column width** | `row.cells[0].width = Cm(1.5)` |

Available built-in table styles: `Light Shading Accent 1`, `Light List Accent 1`, `Medium Shading 1 Accent 1`, `Table Grid`, `Colorful List`, etc.

### Multi-line cells

Use `\n` inside cell text — it converts to new paragraphs in the Google Doc:
```python
cell.text = "Line one\nLine two\nLine three"
```
The `\n` characters become `\x0b` (line break) in the converted Google Doc.

---

## Step 2 — Upload as Google Doc

```python
import sys, os
sys.path.insert(0, '/opt/hermes')
os.environ['HERMES_SESSION_USER_ID'] = '[REDACTED-TID]'

from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')

file_metadata = {
    'name': 'My Document Name',
    'parents': [TARGET_FOLDER_ID],
    'mimeType': 'application/vnd.google-apps.document'
}
media = MediaFileUpload(
    '/tmp/output.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)

uploaded = drive.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, name, webViewLink'
).execute()
doc_id = uploaded['id']
print(f"Created: {uploaded['webViewLink']}")
```

**Important:** The `name` in the body is the final Google Doc name. The body `mimeType` must be `application/vnd.google-apps.document` to trigger conversion. The `MediaFileUpload` `mimetype` is the source file's actual type.

---

## Step 3 — Make URLs clickable (post-conversion)

URL text survives the DOCX→Google Doc conversion but is **not clickable**. Use Docs API:

```python
import re

docs_svc = build_service('docs', 'v1', service_name='google-draas')
doc = docs_svc.documents().get(documentId=doc_id).execute()
body = doc.get('body', {}).get('content', [])

link_requests = []

def find_urls(elements):
    """Recursive: handles paragraphs AND table cells."""
    for elem in elements:
        if 'paragraph' in elem:
            for run in elem['paragraph'].get('elements', []):
                if 'textRun' in run:
                    t = run['textRun'].get('content', '')
                    s = run['startIndex']
                    for match in re.finditer(r'https://[a-zA-Z0-9/._\-?&=]+', t):
                        url = match.group()
                        url_start = s + match.start()
                        url_end = s + match.end()
                        link_requests.append({
                            "updateTextStyle": {
                                "range": {"startIndex": url_start, "endIndex": url_end},
                                "textStyle": {
                                    "link": {"url": url},
                                    "foregroundColor": {"color": {"rgbColor": {"red": 0.06, "green": 0.38, "blue": 0.76}}},
                                    "underline": True
                                },
                                "fields": "link,foregroundColor,underline"
                            }
                        })
        elif 'table' in elem:
            for row in elem['table'].get('tableRows', []):
                for cell in row.get('tableCells', []):
                    find_urls(cell.get('content', []))

find_urls(body)

for i in range(0, len(link_requests), 50):
    docs_svc.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": link_requests[i:i+50]}
    ).execute()
```

### ⚠️ URL Split Across Text Runs (Known Quirk)

After conversion, URLs occasionally SPLIT across adjacent text runs:
```
P[54]: ' https://drive.google.com/.../Yeo1'
P[126]: 'w'
```
The regex only sees the first fragment. To fix, check for orphan continuation characters at boundaries, or delete-and-reinsert the complete URL.

**Fix approach** — merge split URL fragments by deleting the split runs and re-inserting the complete URL as one run, then re-link:
```python
# After detecting a URL split (first fragment linked, continuation orphaned):
correct_url = "https://drive.google.com/.../full_url"
complete_text = f" {correct_url}"

# Delete split fragment range (e.g. 54-126 which has partial URL)
requests = [{"deleteContentRange": {"range": {"startIndex": 54, "endIndex": 130}}}]
requests.append({"insertText": {"location": {"index": 54}, "text": complete_text}})
docs_svc.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

# Then link the re-inserted URL at the new position
url_start = 55  # after the leading space
url_end = url_start + len(correct_url)
requests2 = [{"updateTextStyle": {
    "range": {"startIndex": url_start, "endIndex": url_end},
    "textStyle": {"link": {"url": correct_url}, "foregroundColor": ..., "underline": True},
    "fields": "link,foregroundColor,underline"
}}]
```
**Note:** `deleteContentRange` may fail if it spans paragraph boundaries. If it errors with "Invalid deletion range", the simpler fallback is to leave the split URL as-is — Google Drive URLs often work even missing the trailing character (the server auto-completes short IDs).

### ⚠️ Line break conversion (`\n` → `\x0b`)

When you use `\n` inside python-docx cell text, the DOCX→Google Doc conversion stores it as `\x0b` (vertical tab / line break), NOT as a new paragraph. This means:
- The URL text is preserved but lives inside a single paragraph with embedded line breaks
- Regex-based URL detection (`https://[a-zA-Z0-9/._\-?&=]+`) still works because it matches word characters only
- However, if a URL wraps across a line break AND a text-run boundary simultaneously, the regex may miss the continuation. Check for this if links seem truncated

**Fix:** After the first link pass, manually scan the doc for any `https://` text that has a `link` key in `textStyle` but whose run content ends with something that looks truncated (doesn't end in `/edit`, `/view`, or a standard terminator). Re-link those ranges.

---

## Step 4 — Delete old version (if replacing)

```python
q = f"'{folder_id}' in parents and name = 'My Document Name' and trashed = false"
for f in drive.files().list(q=q, fields='files(id)').execute().get('files', []):
    drive.files().delete(fileId=f['id']).execute()
```

---

## Method Comparison

| Approach | Best for | Don't use for |
|----------|----------|---------------|
| **HTML import** | Rich visual docs with colors, callout boxes, headings | Docs with multiple structured tables |
| **DOCX-from-scratch** (this method) | Structured data displayed in proper tables with clickable links | Heavy visual formatting, colored backgrounds |
| **Template-fill** (.docx from Drive) | Populating an existing branded template (bank forms, letterheads) | Creating a new doc from data (no template exists) |
| **Docs API batchUpdate** | Targeted text edits on existing docs | Creating new tables or complex layouts |

## Practical Example

Used to create a "Resources Reference" document with:
- 2 proper tables (3 cols × 4 rows, 3 cols × 8 rows)
- 8 clickable hyperlinks
- Styled headers with `Light Shading Accent 1` style
- Bullet lists for pending items and red flags
- Centered title and subtitle

---

## Post-Creation: Updating Table Values with `replaceAllText`

When you need to update values in a Google Doc that has tables (e.g., fixing a spec after a plan revision), **`replaceAllText` is dramatically simpler** than `deleteContentRange` + `insertText`:

### ✅ Preferred: `replaceAllText`

Works for **any unique value** regardless of whether it's in a paragraph, table cell, or header:

```python
requests = [
    {"replaceAllText": {
        "containsText": {"text": "1,109.38", "matchCase": True},
        "replaceText": "1,017.39"
    }},
    {"replaceAllText": {
        "containsText": {"text": "FSI: 1.86", "matchCase": True},
        "replaceText": "FSI: 1.83"
    }}
]
result = docs_svc.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
for reply in result.get('replies', []):
    occ = reply.get('replaceAllText', {}).get('occurrencesChanged', 0)
    print(f"Replaced: {occ} occurrence(s)")
```

`replaceAllText` bypasses table-cell index constraints — `deleteContentRange` frequently fails inside table cells with `"Invalid deletion range"` because of how table content ranges are structured.

### When the value isn't unique

Add surrounding context to disambiguate:

```python
# Instead of: "2,781"
# Use: "total built-up area of approximately 2,781 sq. ft."
{"replaceAllText": {
    "containsText": {"text": "total built-up area of approximately 2,781 sq. ft.", "matchCase": False},
    "replaceText": "total built-up area of approximately 2,689 sq. ft."
}}
```

Available built-in table styles: `Light Shading Accent 1`, `Light List Accent 1`, `Medium Shading 1 Accent 1`, `Table Grid`, `Colorful List`, etc.