# GWS: Deliver a formatted Google Doc via Drive HTML-import (avoids Docs API quota)

Session-proven pattern for "build me a Google Doc with tables/headings and give me the link"
(used for the Kelsa misc-budget analysis doc, Aug 2026).

## Why not Docs API batchUpdate
- Docs API write ops are rate-limited to **60/min/user** → any per-cell `insertText` loop
  dies with HTTP 429 "Quota exceeded for quota group for write operations per minute per user".
- `insertText` at the body end must use `endIndex - 1` (error: "Index must be less than the
  end index of the referenced segment").
- Table-cell indices go stale after earlier inserts; a fresh fetch is needed per row unless
  you insert cells in reverse order in ONE batchUpdate.

## Working pattern: build HTML string, import via Drive
```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseUpload
import io

drive = build_service('drive', 'v3', service_name='google-draas')  # resolve first via gws_resolve_account
# Find TMP folder:
#   drive.files().list(q="name='TMP' and mimeType='application/vnd.google-apps.folder' and trashed=false")
# (seen id: 18p74II2uL32sNDzDDwXzmlOUdJJOTmE- — do not hardcode, search fresh)

html = "<html><body>...tables/headings...</body></html>"
media = MediaIoBaseUpload(io.BytesIO(html.encode('utf-8')), mimetype='text/html', resumable=False)
file = drive.files().create(
    body={'name': TITLE, 'mimeType': 'application/vnd.google-apps.document', 'parents': [TMP_FOLDER]},
    media_body=media, fields='id,name,webViewLink').execute()
# returns webViewLink for the share link
```

Key points:
- `MediaIoBaseUpload(io.BytesIO(...), mimetype='text/html')` REQUIRED — raw BytesIO as
  media_body fails with "media_filename must be str or MediaUpload".
- body `mimeType: application/vnd.google-apps.document` converts HTML → native Doc.
- Verify: `files().get(fileId=..., fields='mimeType')` returns application/vnd.google-apps.document.
- HTML tables render as real Doc tables: `<table style="border-collapse:collapse">` +
  `<td style="border:1px solid #999;padding:6px;font-size:11px">`, bold header row.
- Escape `& < >` in all data cells (use a small esc() helper).
- One API call, no quota issue, full formatting.

## Docs API append (when only adding text to existing doc)
- `end = d['body']['content'][-1]['endIndex'] - 1`; insertText at that index.
- For tables: ONE batchUpdate with all insertText requests, iterate cells in REVERSE order
  (last cell first) so computed indices stay valid.

## Cleanup
- After failed partial attempts, duplicate docs with the same name pile up in the folder.
  List `q="name contains '<title>' and trashed=false"`, delete all but the final id.
