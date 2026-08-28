# .docx → Google Doc Conversion via Drive API

When you receive a .docx file (Office Open XML) and need to edit it via the Google Docs API, you must first convert it to a native Google Doc. The Docs API **cannot edit native Office files** — it returns:

> `This operation is not supported for this document. The document must not be an Office file.`

## One-step conversion via Drive copy

The simplest method: copy the file with `mimeType: application/vnd.google-apps.document`:

```python
from tools.gws_auth import build_service

drive = build_service("drive", "v3")

copied = drive.files().copy(
    fileId="ORIGINAL_DOCX_FILE_ID",
    body={
        "name": "Converted Google Doc Name",
        "mimeType": "application/vnd.google-apps.document"
    }
).execute()

new_doc_id = copied["id"]
print(f"Google Doc URL: https://docs.google.com/document/d/{new_doc_id}/edit")
```

Now you can use the Docs API (`build_service("docs", "v1")`) normally with `new_doc_id`.

## Key details

- The original .docx file is **not modified** — a new Google Doc is created
- All content (text, tables, formatting) is preserved in the conversion
- The new Google Doc lives in the same Drive folder as the original
- You can name the copy anything — use a clear naming convention to distinguish it from the original

## Pitfalls

- **The Docs API cannot edit .docx files directly** — always convert first. Attempting `documents().get()` on a .docx file raises HTTP 400.
- **Conversion is not reversible** — converting back to .docx via Drive export is a separate operation (`drive.files().export()` with `mimeType=application/vnd.openxmlformats-officedocument.wordprocessingml.document`).
- **File ownership** — the new Google Doc is owned by the authenticated user (not the original .docx owner). This matters for sharing permissions and folder placement.
- **Google Docs API rate limits apply** — 60 write requests per minute per user. Batch your updates when possible.

## When to use this vs python-docx

| Approach | When |
|----------|------|
| **Drive copy → Google Doc** | Need rich formatting (RED text, table restructuring, cross-document references), need to share with collaborators, or can't install python-docx |
| **python-docx** | Need to preserve .docx format, need to re-upload the edited file to Drive as .docx, or offline editing |
