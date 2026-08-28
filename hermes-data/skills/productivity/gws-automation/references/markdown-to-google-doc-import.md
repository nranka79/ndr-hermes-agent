# Markdown → Google Doc Import

Upload a local `.md` file as an editable Google Doc in one Drive API call.

## Technique

Use `drive.files().create()` with:
- `mimeType` = `application/vnd.google-apps.document` (target format)
- Media file with `mimetype = "text/markdown"` (source format)
- `parents` = target folder ID

Drive converts the markdown automatically — headings, lists, bold, code fences all survive.

## Minimal example

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service("drive", "v3")

media = MediaFileUpload("/tmp/note.md", mimetype="text/markdown")
file_metadata = {
    "name": "Readable Title — Subtitle",
    "mimeType": "application/vnd.google-apps.document",
    "parents": ["FOLDER_ID"]
}

uploaded = drive.files().create(
    body=file_metadata,
    media_body=media,
    fields="id, name, webViewLink"
).execute()

print(uploaded["webViewLink"])
```

## Pitfalls

1. **No inline image support** — markdown images (`![](path)`) are dropped during import. Add images via Docs API after creation.
2. **Tables** — pipe tables survive but may need column-width adjustment in the Doc.
3. **Very long files** (>200KB) may hit Drive API import limits. Split into sections or upload as plain text instead.
4. **Special chars in filenames** — the `name` field becomes the Doc title. Avoid `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`.
5. **FOLDER_ID is required** — Drive API doesn't default to "My Drive" root for programmatic uploads. Always supply `parents`.

## When to use this vs. HTML import

| Scenario | Technique | Reason |
|---|---|---|
| Markdown file on disk | Markdown import (this ref) | Native → best fidelity for MD |
| HTML file on disk | `html-import-to-google-doc` | Drive imports HTML natively |
| HTML generated in-memory | `docs-create-from-html` | Docs API for HTML content |
| Create Doc from scratch | `google-doc-creation-pattern` | Blank doc, then populate via API |
