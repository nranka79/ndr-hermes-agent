# Dossier Rebuild Workflow (session pattern)

From a real session where a medical dossier (v1.3) was rebuilt into a clean v2.0 after the user reported broken links, duplicate data, and a pending lab result that had arrived.

## Trigger

User says: "produce a fresh dossier" / "relook the Google document correctly" / "many of the links were not working" / "wherever there was tabular data on top of it the data was repeating"

## Link verification pattern (recommended)

```python
links_to_check = {
    "friendly_name": "drive_file_id_here",
    "PFT_Dec2025": "1tJoC1v1LV_0Y39Cu2foXmwNr8QMbIbVH",
}

valid_links = {}
for name, file_id in links_to_check.items():
    try:
        f = drive.files().get(fileId=file_id, fields='id, name').execute()
        valid_links[name] = f'https://drive.google.com/file/d/{file_id}/view'
        print(f'  OK: {name} -> {f["name"]}')
    except Exception as e:
        print(f'  BROKEN: {name} -> {e}')
        valid_links[name] = None
```

## Deduplication checklist

When you see these pairs in an existing dossier, remove the narrative version:

| Table in dossier | Paragraph version to remove |
|---|---|
| PFT trend table (FEV1%, FVC%, FEF25-75%) | Bullet-list of each PFT with same values |
| Clinical timeline table (date, event, details) | Paragraph list of each event in same detail |
| Treatment course table (date, provider, changes) | Paragraph list of each visit + medication |
| Key findings table | Bullet-list of each finding with same text |

Exception: Keep analysis/interpretation prose (e.g., "This dissociation between FEV1/FVC and FEF25-75 is the hallmark of small airway disease") — only redundant flat data dumps should go.

## New result incorporation checklist

1. Upload PDF to medical folder
2. Append row to Medical Report Index sheet (if exists): `[Sl.No, TYPE, DATE, REPORT NAME, LINK, REPORT NAME]`
3. Append section to Medical Summary doc
4. Create new dossier version:
   - Replace "pending"/"awaited" markers with actual result + link
   - Add new event to clinical timeline
   - Add new section for the result with interpretation
5. Use **HTML→Google Doc import** for formatting (not Docs API insertText):
   - Build a well-formatted HTML file with CSS (tables with colored headers, alternating rows, callout boxes, status badges, numbered sections)
   - Upload to Drive as `text/html` → `application/vnd.google-apps.document`
   - Fix page layout immediately after: set A4 portrait (595x842 PT) with 1in margins via `updateDocumentStyle`
   - Insert blank lines before each heading: batchUpdate with `insertText` of `\n` at each heading `startIndex`, in reverse order
6. Export PDF + save to folder
7. Deliver both Google Doc link and PDF link
8. Delete old PDF versions from Drive

## HTML→Google Doc page layout fix (required after every import)

```python
# After HTML import creates the doc, fix page to A4 portrait with 1in margins
docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': [{
    'updateDocumentStyle': {
        'documentStyle': {
            'pageSize': {'height': {'magnitude': 842, 'unit': 'PT'}, 'width': {'magnitude': 595, 'unit': 'PT'}},
            'marginTop': {'magnitude': 72, 'unit': 'PT'}, 'marginBottom': {'magnitude': 72, 'unit': 'PT'},
            'marginLeft': {'magnitude': 72, 'unit': 'PT'}, 'marginRight': {'magnitude': 72, 'unit': 'PT'}
        },
        'fields': 'pageSize,marginTop,marginBottom,marginLeft,marginRight'
    }
}]}).execute()
```

## Section spacing fix (required after every HTML import)

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
headings = [el['startIndex'] for el in doc['body']['content']
            if 'paragraph' in el and el['paragraph'].get('paragraphStyle', {}).get('namedStyleType', '').startswith('HEADING_')]
# Process in REVERSE order because insertText shifts subsequent indices
requests = [{'insertText': {'location': {'index': h}, 'text': '\n'}} for h in reversed(headings)]
if requests:
    docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': requests}).execute()
```
