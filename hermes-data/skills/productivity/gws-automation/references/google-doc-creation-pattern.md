# Google Doc Creation with Structured Content (Docs API)

## When to use
Create a structured Google Doc with headers, sections, bullet lists, tables, and horizontal rules programmatically. Used for reports, analysis documents, offer letters, and any deliverable the user wants as a polished Google Doc rather than plain text in chat.

## Pattern — single-batch insert + no-format approach

The simplest and most reliable approach: insert ALL content as a single text blob, then optionally apply formatting in a second batch. This avoids index-shifting bugs entirely.

```python
from tools.gws_auth import build_service
from googleapiclient.discovery import build

# 1. Create blank doc
docs = build_service('docs', 'v1')
doc = docs.documents().create(body={'title': 'Title Here'}).execute()
doc_id = doc['documentId']

# 2. Find end index
doc_obj = docs.documents().get(documentId=doc_id).execute()
end = doc_obj['body']['content'][-1]['endIndex'] - 1

# 3. Insert full content as one batch
full_text = """
EXECUTIVE SUMMARY
...
"""
requests = [{"insertText": {"location": {"index": end}, "text": full_text}}]
docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
```

## Content format conventions

- **Section separator:** `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━` (40x U+2501)
- **Main headings:** `1. SECTION HEADER` (numbered)
- **Bullets:** `• Item` (U+2022)
- **Key-value:** `• **Label:** Value`

## Moving doc to a folder

```python
drive = build_service('drive', 'v3')
drive.files().update(fileId=doc_id, addParents='<folder_id>', removeParents='root', fields='id,parents').execute()
```

## Pitfalls

1. **Docs API vs Drive HTML upload:** `drive.files().create()` with HTML mimeType conversion creates docs where `docs.documents().get()` returns EMPTY paragraph text. Always use Docs API for programmatic creation.
2. **Index shifting:** Do ALL inserts in a single batch. For multi-batch: deletes DESC, then re-read doc for current indices, then inserts ASC.
3. **No markdown auto-formatting:** The Docs API writes raw text. Bold/headings require separate `updateParagraphStyle` / `updateTextStyle` requests with computed ranges.
4. **Appending to existing doc:** Use `end = doc['body']['content'][-1]['endIndex'] - 1`

## Proven section template (from compensation review)

| Section | Content |
|---------|---------|
| EXECUTIVE SUMMARY | 1-paragraph overview |
| 1. EMPLOYEE PROFILE | Name, email, tenure, salary structure |
| 2. SALARY HISTORY | Timeline: date → structure → total |
| 3. WORK SCOPE ANALYSIS | Sub-sections per role area |
| 4. COMMUNICATION PATTERN | Data-driven observations |
| 5. INTERNAL COMPARISON | Chennai CTC sheet data |
| 6. MARKET BENCHMARKS | Industry data with cited sources |
| 7. COMPANY CONTEXT | Turnover projections |
| 8. LOANS & ADVANCES | Pending data section |
| 9. RECOMMENDATIONS | Proposed structure + rationale |
| 10. NEXT STEPS | Action items |
| 11. COMPENSATION ANALYSIS | Supporting data + verdict |
| SOURCES & REFERENCES | Cited URLs |
