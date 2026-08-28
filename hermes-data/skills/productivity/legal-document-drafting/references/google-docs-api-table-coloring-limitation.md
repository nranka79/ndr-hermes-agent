# Google Docs API — Table Cell Formatting Limitation & Red Color Workaround

## The Problem

When `documents.get()` is called on a Google Doc containing tables, **all text runs inside table cells report `startIndex: 0, endIndex: 0`**:

```python
result = docs.documents().get(documentId=DOC_ID).execute()
content = result['body']['content']

# Table cell text runs all return:
# {'startIndex': 0, 'endIndex': 0, 'textRun': {'content': '1486', ...}}
```

This means `batchUpdate` with `updateTextStyle` targeting table cell runs will fail or apply to wrong positions — **table cell text runs cannot be individually formatted via the Google Docs API**.

## The Working Approach

**Paragraph-level text runs (outside tables) have valid indices:**

```python
result = docs.documents().get(documentId=DOC_ID).execute()
content = result['body']['content']

all_runs = []
def traverse(elem, path=""):
    if isinstance(elem, dict):
        if 'textRun' in elem:
            tr = elem['textRun']
            txt = tr.get('content', '')
            si = elem.get('startIndex')
            ei = elem.get('endIndex')
            if txt and txt.strip():
                all_runs.append({'start': si, 'end': ei, 'text': txt, 'path': path})
    # ... recurse into paragraph and table elements

# Find runs containing target values
target_values = ['27544.00', '1486', '1518', ...]
runs_to_color = [r for r in all_runs if any(v in r['text'] for v in target_values)]

# Apply red (RGB 1.0, 0.0, 0.0) to each run
requests = []
for run in runs_to_color:
    if run['start'] and run['end'] and run['start'] != run['end']:
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': run['start'], 'endIndex': run['end']},
                'textStyle': {'foregroundColor': {'color': {'rgbColor': {'red': 1.0, 'green': 0.0, 'blue': 0.0}}}},
                'fields': 'foregroundColor'
            }
        })

docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': requests}).execute()
```

**Result this session:** 43 runs colored red — all non-table paragraph values successfully updated.

## What Fails

| Approach | Result |
|----------|--------|
| `batchUpdate` on table cell runs | Fails silently — `startIndex: 0, endIndex: 0` prevents targeting |
| `replaceAllText` | Works for text replacement only — CANNOT apply formatting |
| Upload DOCX then format | Google Docs conversion strips red formatting |
| `drive.files().update()` with revised DOCX | Converts to Google Docs format — strips all formatting |

## Workarounds for Table Cells

1. **Accept partial coloring** — color the paragraph-level summary values (totals, clause text) red; leave table cell individual numbers uncolored. This is what was done this session.

2. **Provide the corrected DOCX file** — the local `Ranka_Amber_SSA_RedCorrected.docx` (43 runs red) is available in `/data/hermes/cron/output/`. User can download from Drive and open in Word.

3. **Split table cell runs** — `batchUpdate` with `insertText` then `deleteContentRange` can theoretically split a table cell's text into separate runs. This is complex and was not attempted.

## Key Code Pattern

```python
# Identify and color all non-table runs with corrected values
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/data/hermes/google_token.json') as f:
    creds = Credentials.from_authorized_user_info(json.load(f))

docs = build('docs', 'v1', credentials=creds)
DOC_ID = '1EnY77qQ-UXeMV7Pr49l6kiK_RTITK_jQ09gvljTthWI'

result = docs.documents().get(documentId=DOC_ID).execute()
content = result['body']['content']

# Traverse and collect all valid runs
all_runs = []
def traverse(elem):
    if 'textRun' in elem:
        txt = elem['textRun'].get('content', '')
        si = elem.get('startIndex')
        ei = elem.get('endIndex')
        if txt.strip() and si and ei and si != ei:
            all_runs.append({'start': si, 'end': ei, 'text': txt})
    for child in elem.get('paragraph', {}).get('elements', []):
        traverse(child)
    for row in elem.get('table', {}).get('tableRows', []):
        for cell in row.get('tableCells', []):
            for c in cell.get('content', []):
                for p in c.get('content', []):
                    for e in p.get('elements', []):
                        traverse(e)

for item in content:
    traverse(item)

# Filter to runs with target values (corrected figures)
target_values = ['27544.00', '2558.9', '1112.6', '11976.00', '11652.00', 
                 '1486', '1518', '1288', '1058', '1313', '1570', '1605', '1380', '1141', '1413']
runs_to_color = [r for r in all_runs if any(v in r['text'] for v in target_values)]

# Apply red
requests = [{'updateTextStyle': {'range': r, 'textStyle': {'foregroundColor': 
              {'color': {'rgbColor': {'red': 1.0, 'green': 0.0, 'blue': 0.0}}}}, 'fields': 'foregroundColor'}} 
             for r in [{'startIndex': run['start'], 'endIndex': run['end']} for run in runs_to_color]]

docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': requests}).execute()
print(f"Colored {len(requests)} runs red")
```

## Token Refresh Pattern

If API returns `401 Unauthorized`:

```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

with open('/data/hermes/google_token.json') as f:
    creds = Credentials.from_authorized_user_info(json.load(f))

if creds.expired:
    Request().refresh(creds)
    # Save refreshed token
    import tokenstore
    tokenstore.save('google_token.json', creds)

# Re-build service
docs = build('docs', 'v1', credentials=creds)
```