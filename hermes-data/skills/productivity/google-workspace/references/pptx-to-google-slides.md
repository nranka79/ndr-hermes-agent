# PPTX → Native Google Slides Conversion

Convert PowerPoint files (.pptx) into native Google Slides (for further editing in the browser) when LibreOffice is unavailable. Uses the Drive API import feature.

**Different from `references/pptx-to-pdf-via-drive.md`:** That reference covers PPTX → PDF export. This one covers PPTX → native Google Slides (editable in browser), plus the reverse (Google Slides → PPTX download).

## Workflow

### PPTX → Google Slides (via Drive API)

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')

# Upload PPTX and convert to Google Slides in one step
media = MediaFileUpload(
    '/path/to/file.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True
)

body = {
    'name': 'Presentation Name',
    'mimeType': 'application/vnd.google-apps.presentation'  # Triggers conversion!
}

result = drive.files().create(
    body=body,
    media_body=media,
    fields='id, name, mimeType, webViewLink'
).execute()

slides_id = result['id']
print(f"Google Slides URL: {result['webViewLink']}")
```

### Google Slides → PPTX Download

```python
# Export as PPTX
pptx_bytes = drive.files().export(
    fileId=slides_id,
    mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'
).execute()

with open('/tmp/output.pptx', 'wb') as f:
    f.write(pptx_bytes)
```

Alternatively via `gws_skill_bridge`:
```python
from tools import gws_skill_bridge
result = gws_skill_bridge.call('drive_download', service_name='google-draas',
    file_id='PRESENTATION_ID',
    output='/tmp/output.pptx',
    export_mime='application/vnd.openxmlformats-officedocument.presentationml.presentation')
```

### Editing the PPTX Before Upload (python-pptx)

Since the Google Slides API requires separate enablement (see Known Issues below), the preferred workflow for programmatic edits is:

1. Download original as PPTX via Drive export
2. Edit with `python-pptx`
3. Upload as new Google Slides via Drive import (above)
4. Share with collaborators

```python
# Step 1: Download
from pptx import Presentation
prs = Presentation('/tmp/original.pptx')

# Step 2: Edit shapes
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if 'Old Text' in run.text:
                        run.text = run.text.replace('Old Text', 'New Text')

prs.save('/tmp/edited.pptx')
```

### Sharing After Upload

```python
permission = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': 'user@example.com'
}
drive.permissions().create(
    fileId=slides_id,
    body=permission,
    sendNotificationEmail=True,
    emailMessage='Updated presentation with verified data'
).execute()
```

## Known Issues

### 1. Google Slides API NOT Enabled by Default

The Google Slides API (`slides.googleapis.com`) is a **separate API** from the Drive API (`drive.googleapis.com`). Most Google Cloud projects enable Drive API but NOT the Slides API. Attempting to use `build_service('slides', 'v1')` returns:

```
HttpError 403: Google Slides API has not been used in project X before or it is disabled.
```

**Workaround:** Do NOT use the Slides API for text updates. Instead:
- Edit the PPTX locally with `python-pptx`
- Upload as new Google Slides via Drive import
- The PPTX → Slides conversion preserves all text changes

This avoids needing the Slides API entirely.

### 2. `gws_skill_bridge` Parameter Quirks

The bridge's `drive_search`, `drive_download`, and `drive_upload` wrappers have specific parameter naming:

| Operation | Correct params | Common mistake |
|-----------|---------------|----------------|
| `drive_search` | `query`, `raw_query=True`, `max=N` | Forgetting `raw_query` or `max` |
| `drive_download` | `file_id`, `output=`, `export_mime=` | Forgetting `output` path |
| `drive_upload` | `path=`, `mime_type=`, `name=`, `parent=` | Using `file_path` instead of `path`; forgetting `parent` |

**Full reference:** See `gws-automation` skill → `references/gws-skill-bridge-drive-operations.md`.

### 3. Format Fidelity

Complex animations, embedded fonts, speaker notes, and transition effects may not survive the PPTX → Slides conversion. For exact layout preservation without conversion, keep the file as PPTX on Drive.

### 4. Ownership

The converted file is owned by the authenticated Google account (e.g., `ndr@draas.com`), not the person you're chatting with. Share with them as `writer` if they need editing access.

### 5. PPTX → Google Slides (not PDF)

The key MIME type `application/vnd.google-apps.presentation` triggers Drive to convert the uploaded PPTX into a native Google Slides file. Without it, the file stays as a PPTX binary blob that opens as "view-only" in Google Drive.

The reverse (export) MIME type for PPTX is `application/vnd.openxmlformats-officedocument.presentationml.presentation`.

## When to Use This vs Alternative Approaches

| Approach | Best for | Limitations |
|----------|----------|-------------|
| **PPTX → Slides import** | Text/table-heavy slides needing further browser editing | Loses complex animations |
| **Slides API (build_service)** | Minimal text-only updates on existing Slides | Need API enablement; no batch text replacement pattern |
| **Google Apps Script** | Complex batch operations | Needs deployment; slow |
| **LibreOffice CLI** | Exact format preservation | May not be installed in container |
