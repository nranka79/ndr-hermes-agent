# Create Richly Formatted Google Doc from HTML

Google Docs API formatting is notoriously fiddly (index management, batch requests, style ranges). An alternative approach: **upload an HTML file and convert it to Google Docs format** via the Drive API.

## The Technique

```python
from googleapiclient.http import MediaFileUpload

# Upload HTML and convert to Google Doc
media = MediaFileUpload('file.html', mimetype='text/html', resumable=True)
doc = drive.files().create(
    body={
        'name': 'My Formatted Document',
        'mimeType': 'application/vnd.google-apps.document',  # ← KEY
        'parents': [FOLDER_ID]
    },
    media_body=media,
    fields='id,name,webViewLink'
).execute()
doc_id = doc['id']
doc_url = doc['webViewLink']
```

## What Preserves Well

| HTML Element | Google Doc Result |
|---|---|
| `<h1>` through `<h6>` | Headings with hierarchy |
| `<table>` with `<tr>`/`<td>` | Tables with rows and cells |
| `<b>`/`<strong>`, `<i>`/`<em>` | Bold, italic |
| `<a href="...">` | Clickable hyperlinks |
| `<ul>`/`<ol>` | Bullet / numbered lists |
| `style="color: #1c5499"` | Text color |
| `style="background: #f7f9fc"` on `<tr>` | Row background color |
| `border: 1px solid #ccc;` on `<td>` | Cell borders |
| `width: 100%` on tables | Full-width tables |

## What Gets Dropped or Distorted

| HTML Feature | Google Doc Behavior |
|---|---|
| `border-radius`, `box-shadow` | Dropped (no effect) |
| `<div>` with background color | Some convert, some drop — prefer styling on `<tr>`/`<td>` instead |
| CSS classes (`<style>...</style>`) | Work inconsistently — prefer **inline styles** on each element |
| `<b>` inside long table cell text | Can cause that table row to be dropped entirely! Avoid `<b>` in long `<td>` text |
| `rowspan`/`colspan` | Often misaligned |
| `<br>` inside table cells | May add spurious paragraph breaks |
| `style="background: #f7f9fc;"` on `<tr>` for alternating rows | Works for most rows but very long rows may drop. Safer: no row backgrounds |

## Known Pitfalls

- **Long table rows with complex formatting** — Google Docs HTML import can drop table rows that contain `<b>` tags inside long cell text (>200 chars). If a row keeps disappearing, remove all `<b>` tags from that row's cells.
- **Background colors on `<tr>`** — Work for short rows but long rows may drop. When a row is critical, use no background color or style individual `<td>` elements instead.
- **Max table size** — Tables with 10+ rows and mixed formatting may have some rows silently dropped. Keep tables focused.
- **Duplicate rows** — The import doesn't silently deduplicate, but can drop rows that exceed size thresholds.
- **Test incrementally** — After import, verify all rows are present by reading the doc back with the Docs API.

## Verification After Import

```python
# Read back to verify all content made it
doc = docs.documents().get(documentId=doc_id).execute()
text = ""
for element in doc['body']['content']:
    for elem in element.get('paragraph', {}).get('elements', []):
        tr = elem.get('textRun', {})
        if 'content' in tr:
            text += tr['content']

# Check for key terms
checks = ['Term1', 'Term2', ...]
for c in checks:
    if c.lower() in text.lower():
        print(f"✅ {c}")
    else:
        print(f"❌ {c} MISSING")
```

## Alternative: Start with Plain Text Doc, Then Style

If HTML import fails for complex content, fall back to:
1. Create an empty Google Doc
2. Insert all content as plain text via `insertText`
3. Apply paragraph / text styles via `updateTextStyle` / `updateParagraphStyle` batch requests

This is more reliable but significantly more code — the Docs API requires precise index management.
