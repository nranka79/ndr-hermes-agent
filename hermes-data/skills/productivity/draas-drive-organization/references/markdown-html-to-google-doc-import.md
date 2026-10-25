# Markdown / HTML → Native Google Doc import (Drive API)

Verified 2026-09-13 (Hesthetic call-script upload). How to get a local .md file
onto Drive as a REAL Google Doc with content, reliably, and how to verify it
actually landed — without being fooled by the Docs API's response shape.

## The failure: markdown import creates a silent EMPTY doc

```python
media = MediaFileUpload('/tmp/notes.md', mimetype='text/markdown')
doc = svc.files().create(
    body={'name': 'Name', 'mimeType': 'application/vnd.google-apps.document',
          'parents': [folder_id]},
    media_body=media, fields='id,name,mimeType,parents').execute()
```

This SUCCEEDS (returns a doc id, correct mimeType, correct parents) but the
doc's body can be **completely empty** (0 chars). Nothing errors; the API
pretends the conversion worked. The upload must be verified by reading the doc
back — never trust the create response.

## The fix: convert to HTML first, import as text/html

The `markdown` python module IS installed in the Hermes venv
(`/opt/hermes/.venv/bin/python3`). Use it, then import the HTML:

```python
import markdown
html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
with open('/tmp/out.html', 'w') as f:
    f.write(html)

media = MediaFileUpload('/tmp/out.html', mimetype='text/html')
doc = svc.files().create(
    body={'name': '20260913_Entity_Description',          # YYYYMMDD convention
          'mimeType': 'application/vnd.google-apps.document',
          'parents': [folder_id]},
    media_body=media, fields='id,webViewLink').execute()
```

HTML import preserves headers, bold, tables ('tables' extension), and the
internal links. This path produced a full doc (16,184 chars) where the
markdown path produced 0.

## Verification — recursive walker, NOT a top-level join

**Pitfall that almost deleted a GOOD doc:** a naive extractor like

```python
text = ''.join(p.get('text','') for p in d['body']['content'] if 'paragraph' in p)
```

returns `0` chars even when the doc is fine — paragraph runs live in
`paragraph['elements'][i]['textRun']['content']` (not `p['text']`), and table
content lives nested under `table['tableRows'][]['tableCells'][]['content']`.
Reading top-level elements only falsely signals a failed import. Use the
recursive walker:

```python
docs_svc = build('docs', 'v1', credentials=creds)
d = docs_svc.documents().get(documentId=doc['id']).execute()

full = []
def walk(elem):
    if 'paragraph' in elem:
        full.append(''.join(r.get('textRun',{}).get('content','')
                            for r in elem['paragraph'].get('elements',[])))
    if 'table' in elem:
        for row in elem['table'].get('tableRows',[]):
            for c in row.get('tableCells',[]):
                for pe in c.get('content',[]):
                    walk(pe)
for e in d['body']['content']:
    walk(e)
joined = '\n'.join(full)
print("TOTAL CHARS:", len(joined))
for k in ['SECTION A', 'SECTION B']:                      # key-section spot check
    print(k, '->', k.lower() in joined.lower())
```

Two cheap extra sanity signals before the walker:
- `svc.files().get(fileId=doc['id'], fields='id,name,size,mimeType')` — a
  non-trivial `size` (e.g. 12,048 bytes) means content exists.
- If a genuinely empty doc WAS created, `svc.files().delete(fileId=...)` then
  re-import; do not leave the empty doc in the folder.

## Folder creation pattern used (Personal > Investment Opportunities > X)

- Find existing folders by `name = '<Name>' and mimeType =
  'application/vnd.google-apps.folder' and trashed = false` — multiple hits
  possible; pick by parent chain (see `permission-patterns.md`).
- Create missing last-level folder with
  `{'name': ..., 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}`
- Verify `parents` contains the intended folder AFTER upload (Hesthetic doc
  verified in `1nipLtcVZ0XbyLl-Z9GYALpoCRNFbjzC7`).