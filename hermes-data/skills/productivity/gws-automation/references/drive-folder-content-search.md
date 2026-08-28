# Cross-Document Text Search within a Drive Folder

Search the *text content* of every Google Doc in a specific Drive folder for keywords, clause references, amounts, or document numbers. Use this when you need to find "which document mentions this cheque number / clause / party name / amount" across a batch of related legal documents.

## When to use this vs other search methods

| Method | What it finds | Best for |
|--------|---------------|----------|
| `drive.files().list(q=...)` | File names, mimeType, date | Finding files by naming convention |
| `drive-comprehensive-search` ref | File metadata + folder traversal | Locating files across Drive |
| **This method** | Text *inside* Google Docs | Finding specific clauses, amounts, cheque numbers, party names across many documents |

## The pattern

```python
from tools.gws_auth import build_service
svc = build_service('drive', 'v3')

# 1. List all Google Docs in the target folder
items = svc.files().list(
    q='"FOLDER_ID" in parents',
    fields="files(id,name,mimeType)",
    pageSize=100
).execute()

# 2. For each Google Doc, export as plain text and search
for f in items.get('files', []):
    if f.get('mimeType') != 'application/vnd.google-apps.document':
        continue  # skip PDFs, sheets, etc.
    
    doc = svc.files().export(fileId=f['id'], mimeType='text/plain').execute()
    content = doc.decode('utf-8') if isinstance(doc, bytes) else doc
    
    # 3. Search line-by-line, print matches with document name + line number
    for i, line in enumerate(content.split('\n')):
        if keyword in line.lower():
            print(f"[{f['name']}] Line {i}: {line.strip()[:200]}")
```

## Keyword selection tips

- Search both figure and word forms: `'1,00,00,000'` and `'one crore'` and `'1 crore'`
- Search partial cheque numbers when the full number might be split: `'001027'` or `'cheque no'`
- Search abbreviations: `'chq'`, `'cheque'`, `'check'`
- Lowercase both sides: `line.lower()` with lowercase keyword

## Gotchas from real usage

- **text/plain export preserves line breaks** — the content is the raw text rendering, not WYSIWYG. Lines may be broken mid-sentence. Always search across the full content, not just visual paragraphs.
- **Blank cheque numbers are common** — in legal docs in drafting stage, cheque numbers are often left as `________` or `[_______________]` and filled in later. Search both the completed and blank patterns.
- **Different doc versions may restructure payment descriptions** — one version might say "paid to the Second Partner towards withdrawal of his excess capital" while another says "paid to the Firm's bank account." Search for the amount, not the description.
- **Drive API query syntax** — use `'"' + FOLDER_ID + '" in parents'` as the query string. The single-outer/double-inner quote wrapping matters.
- **Large folders** — set `pageSize=100` or use `nextPageToken` for folders with 100+ files. Filter by mimeType early to skip non-Doc exports.

## Script pattern (temp file avoids quoting errors)

Always write a temp Python script to `/tmp/` and execute it, rather than using inline `python -c '...` which breaks on f-strings with escaped quotes:

```python
# Instead of terminal("python -c '...'") with escaping nightmares:
write_file content='''
#!/opt/hermes/.venv/bin/python
import sys; sys.path.insert(0, '/opt/hermes')
import os; os.environ['HERMES_HOME'] = '/data/hermes'
from tools.gws_auth import build_service
svc = build_service('drive', 'v3')
# ... full logic with f-strings, loops, nested quotes ...
''' to '/tmp/search_docs.py'

terminal('chmod +x /tmp/search_docs.py && HERMES_HOME=/data/hermes /tmp/search_docs.py')
```

This completely avoids the quoting issues with f-strings, nested quotes, and special characters in shell commands.
