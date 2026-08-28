# HTML → Google Doc Import (via Drive API)

Import a richly formatted HTML file as a Google Doc, preserving tables, colors, bold/italic, links, and lists. This is the most reliable way to create a polished Google Doc without wrestling with the Docs API's batchUpdate index management.

## When to use

- You need a Google Doc with **styled tables, colored backgrounds, highlighted boxes, bullet lists, and inline links**
- The Docs API's `batchUpdate` with index tracking is too error-prone for complex layouts
- You want **version history** (automatic in Google Docs)

## How it works

Upload an HTML file to Drive with `mimeType='text/html'` and specify `mimeType='application/vnd.google-apps.document'` in the body. Drive converts it server-side to a native Google Doc.

## Pattern

```python
import sys
sys.path.insert(0, '/opt/hermes/tools')
from gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', telegram_id='USER_TELEGRAM_ID')

# Upload HTML → convert to Google Doc
media = MediaFileUpload('/path/to/file.html', mimetype='text/html', resumable=True)

doc = drive.files().create(
    body={
        'name': 'Doc Title Here',
        'mimeType': 'application/vnd.google-apps.document',
        'parents': ['FOLDER_ID']  # optional
    },
    media_body=media,
    fields='id,name,webViewLink'
).execute()

doc_id = doc['id']
doc_url = doc['webViewLink']

# Set sharing
drive.permissions().create(
    fileId=doc_id,
    body={'type': 'anyone', 'role': 'reader'},
    fields='id'
).execute()

print(f"Doc: {doc_url}")
```

## HTML → PDF export (from the doc)

```python
import io
from googleapiclient.http import MediaIoBaseDownload

pdf_bytes = io.BytesIO()
request = drive.files().export_media(fileId=doc_id, mimeType='application/pdf')
downloader = MediaIoBaseDownload(pdf_bytes, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/path/to/output.pdf', 'wb') as f:
    f.write(pdf_bytes.getvalue())
```

## HTML guidelines for best conversion

| HTML element | Google Doc result |
|---|---|
| `<table>` with `<th>` | Native Google Doc table with header row |
| `style="background: #1c5499"` on `<th>` | Blue header background |
| `style="background: #f7f9fc"` on `<tr>` | Alternating row colors |
| `<div style="background: ...; border-left: 4px solid ...">` | Colored callout boxes (approximation) |
| `<a href="...">` | Clickable hyperlinks |
| `<b>` / `<i>` | Bold / italic |
| `<ul><li>` | Bullet lists |
| `style="color: #1c5499"` on `<h1>` | Colored headings |

## Limitations

| Limitation | Workaround |
|---|---|
| Complex nested CSS (classes, external stylesheets) | Use **inline styles** (`style="..."`) instead |
| Very long table rows with mixed bold spans inside cells may be dropped | Simplify cell content — use plain text or `<b>` only on short phrases |
| Row-level `background` on `<tr>` may not survive | Add `background` directly to each `<td>` or `<th>` |
| `border-radius`, `box-shadow` not supported | Ignored gracefully; use plain borders |
| Images with relative paths | Use absolute URLs for images |

## Pitfall: Google Docs index tracking in batchUpdate

Avoid using the Docs API `documents().batchUpdate()` for initial content creation when you have complex formatting — the index management is fragile. Use the HTML import approach above, then use `batchUpdate` only for small additions (e.g., inserting a correction paragraph at a known position).

To insert text at the end of an existing doc:

```python
docs = build_service('docs', 'v1', telegram_id='USER_TELEGRAM_ID')
doc = docs.documents().get(documentId=doc_id).execute()
end_idx = doc['body']['content'][-1]['endIndex'] - 1

docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'insertText': {
            'location': {'index': end_idx},
            'text': '\\n\\nNew content here'
        }
    }]}
).execute()
```
