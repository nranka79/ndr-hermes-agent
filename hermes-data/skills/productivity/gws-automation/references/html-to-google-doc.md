# HTML → Google Doc (Rich Formatting via Import)

The Google Docs API's `batchUpdate` with index management is error-prone for richly formatted documents (colored tables, styled divs, highlights, etc.). A **far simpler and more reliable** approach: upload an HTML file via the Drive API and convert it to Google Docs format in one call.

## Technique

```python
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', telegram_id='USER_TELEGRAM_ID')

media = MediaFileUpload('/path/to/file.html', mimetype='text/html', resumable=True)

body = {
    'name': 'My Richly Formatted Document',
    'mimeType': 'application/vnd.google-apps.document',  # ← converts to Google Doc
    'parents': [TARGET_FOLDER_ID]  # optional
}

doc = drive.files().create(body=body, media_body=media, fields='id,name,webViewLink').execute()
doc_id = doc['id']
doc_url = doc['webViewLink']
```

## What HTML/CSS Survives the Conversion

| Feature | Supported? | Notes |
|---|---|---|
| `<h1>`–`<h6>` with inline `color` | ✅ | Preserves font size hierarchy + color |
| `<table>` with `<th>`, `<tr>`, `<td>` | ✅ | Tables convert to native Google Docs tables |
| `border-collapse`, `border` on table | ✅ | Borders preserved |
| `background`/`background-color` on `<tr>` or `<td>` | ✅ | Row/header colors preserved |
| `style="color: #..."` on any tag | ✅ | Text color preserved |
| `font-weight: bold` / `<b>` / `<strong>` | ✅ | Bold preserved |
| `font-style: italic` / `<i>` / `<em>` | ✅ | Italic preserved |
| `<a href="...">` links | ✅ | Hyperlinks preserved, clickable in Doc |
| `<ul>/<ol>` with `<li>` | ✅ | Lists preserved |
| `<div>` with `background` + `border` | ⚠️ Partially | Background color works; `border-radius` may not render |
| `border-left: 4px solid #color` on div | ⚠️ | May lose the thick left-border effect (use table for critical styling) |
| `@page` CSS or `@media print` | ❌ | Not supported; Doc uses its own page model |
| `<style>` block in `<head>` | ⚠️ | Inline `style="..."` attributes are MUCH more reliable than `<style>` blocks |
| CSS classes | ❌ | Use **inline styles only** (`style="..."` on each element) |
| Embedded `<img>` with `src` | ⚠️ | Some images survive; prefer Drive-hosted images with links |

## Best Practices for Maximum Fidelity

1. **Inline styles only** — Every `style="..."` attribute directly on the element. `<style>` blocks often get dropped.

2. **Table-first layout** — For colored sidebars, highlight boxes, and callout panels, use a single-cell `<table>` with background color rather than `<div>` with borders. Tables convert more faithfully.

3. **Flat structure** — Avoid deeply nested `<div>` trees. Flat `<table> → <tr> → <td>` hierarchies convert cleanly.

4. **Hyperlinks** — Use `<a href="...">` with `style="color:#1c5499"` for link-colored text. Docs preserves the URL.

5. **Version history** — Google Docs automatically enables version history. Users can: `File → Version history → See version history` to track changes.

## Why Not Use the Docs API Directly?

The Docs API `batchUpdate` requires:
- Manual index tracking across all insertions
- Separate style application requests referencing exact character ranges
- Complex table creation with `createTable` + column-by-column content insertion
- Frequent `Invalid requests[N].insertText: Index X must be less than the end index` errors

The HTML import approach avoids all of this — one upload call, full formatting preserved.

## Pitfalls

- **Doc size limits**: Very large HTML files (>1 MB) may truncate. Keep the HTML under 500 KB.
- **Unsupported CSS**: `flexbox`, `grid`, `position`, `float` — none of these work. Stick to table-based layout.
- **Font embedding**: Custom web fonts (`@font-face`) won't load. Use `font-family: Arial, Helvetica, sans-serif` — system fonts only.
- **Character encoding**: Always use `<meta charset="utf-8">` as the first element in `<head>`. Non-ASCII characters (em-dash, accents, non-Latin scripts) will be garbled otherwise.
- **Subsequent edits**: After the initial HTML import, further edits should go through the Docs API or manual editing in the Doc. Re-uploading HTML creates a new Doc — use `drive.files().update()` with the same media upload to replace content of an existing Doc.
