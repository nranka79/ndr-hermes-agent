# HTML Import to Google Docs — Formatting-First Approach

## Why HTML Import Instead of Docs API

The Google Docs API's primary content-insertion method — `batchUpdate(insertText)` — inserts **bare plain text with zero formatting**. To add formatting, you need a second pass of `updateTextStyle`, `updateParagraphStyle`, etc. This is:
- 3-5× more API calls than HTML import
- Nearly impossible for complex tables
- Painful for colored/alternating rows
- Error-prone for hyperlinks in table cells

HTML import (`drive.files().create` with `mimeType='text/html'` and target `mimeType='application/vnd.google-apps.document'`) preserves:
- `<h1>`-`<h6>` → proper heading styles
- `<table>` → real Docs tables with borders
- `<tr style="background:...">` → colored rows (alternating works)
- `<a href="...">` → clickable hyperlinks
- `<span style="color:...">` → colored text
- CSS `margin`, `padding`, `border` → approximate layout
- Inline CSS class-based badges and callout boxes

## Procedure

### Step 1: Build the HTML

Use a well-structured HTML document with embedded `<style>` block. For clinical dossiers, the `clinical-dossier` skill has a template at `templates/dossier-html-import-template.html`.

Key CSS patterns that survive import:
```css
/* Tables with colored headers */
th { background: #075e54; color: #fff; }
tr:nth-child(even) td { background: #f5faf9; }
/* Info boxes */
.info-box { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 12px; }
.result-box { background: #e8f5e9; border-left: 4px solid #4caf50; padding: 12px; }
```

### Step 2: Import to Google Docs

```python
from googleapiclient.http import MediaIoBaseUpload
import io

media = MediaIoBaseUpload(
    io.BytesIO(html_content.encode('utf-8')),
    mimetype='text/html',
    resumable=True
)

doc_file = drive.files().create(
    body={
        'name': 'Document Title',
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [FOLDER_ID]
    },
    media_body=media,
    fields='id, name, webViewLink'
).execute()
```

### Step 3: REQUIRED — Fix Page Layout

HTML import often produces landscape or wrong page size. Always fix within the same session:

```python
docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': [{
    'updateDocumentStyle': {
        'documentStyle': {
            'pageSize': {
                'height': {'magnitude': 842, 'unit': 'PT'},   # A4 portrait
                'width': {'magnitude': 595, 'unit': 'PT'}
            },
            'marginTop': {'magnitude': 72, 'unit': 'PT'},     # 1 inch
            'marginBottom': {'magnitude': 72, 'unit': 'PT'},
            'marginLeft': {'magnitude': 72, 'unit': 'PT'},
            'marginRight': {'magnitude': 72, 'unit': 'PT'}
        },
        'fields': 'pageSize,marginTop,marginBottom,marginLeft,marginRight'
    }
}]}).execute()
```

### Step 4: REQUIRED — Fix Section Spacing

HTML import renders sections without any blank line between them. The user will complain that text runs together. Fix by inserting `\n` before each heading:

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
headings = [
    el['startIndex'] for el in doc['body']['content']
    if 'paragraph' in el
    and el['paragraph'].get('paragraphStyle', {}).get('namedStyleType', '').startswith('HEADING_')
]
requests = [
    {'insertText': {'location': {'index': h}, 'text': '\n'}}
    for h in reversed(headings)
]
if requests:
    docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': requests}).execute()
```

### Step 5: Export to PDF

```python
pdf_content = drive.files().export(fileId=DOC_ID, mimeType='application/pdf').execute()
pdf_file = drive.files().create(
    body={'name': 'Document Title.pdf', 'parents': [FOLDER_ID]},
    media_body=MediaIoBaseUpload(io.BytesIO(pdf_content), mimetype='application/pdf')
).execute()
```

## Limitations

- Google's HTML→Doc converter has known quirks with deeply nested tables and certain CSS properties
- Long table cell content with bold/span combinations may be silently dropped — keep cell text plain for long entries
- CSS `display: flex` is NOT supported — use tables for side-by-side layouts
- CSS `border-radius` on boxes is approximated or ignored
- Google Docs has no concept of CSS classes — all styling is inline after import
- Empty `<h2>` elements may be created from CSS artifacts — verify the document after import
