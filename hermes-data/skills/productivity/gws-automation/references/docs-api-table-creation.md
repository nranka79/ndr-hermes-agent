# Google Docs API — Table Creation

Creating tables via the Google Docs `batchUpdate` API requires careful index management. This reference covers the verified pattern for inserting tables and populating cells.

## Step 1 — Insert the Table

```python
from tools.gws_auth import build_service
docs = build_service('docs', 'v1')

requests = [{
    'insertTable': {
        'rows': 11,       # header + 10 data rows
        'columns': 2,
        'location': {
            'index': 17653  # position in the document where the table goes
        }
    }
}]

result = docs.documents().batchUpdate(
    documentId=DOC_ID,
    body={'requests': requests}
).execute()
```

The table is inserted at the specified index. Each cell initially contains a single `\n` character.

## Step 2 — Get Cell Indices

After table insertion, read the document to find each cell's text-start index:

```python
doc = docs.documents().get(documentId=doc_id).execute()
body = doc.get('body', {}).get('content', [])

for elem in body:
    if 'table' in elem:
        rows = elem['table'].get('tableRows', [])
        for ri, row in enumerate(rows):
            cells = row.get('tableCells', [])
            for ci, cell in enumerate(cells):
                for ce in cell.get('content', []):
                    if 'paragraph' in ce:
                        for pe in ce['paragraph'].get('elements', []):
                            if 'textRun' in pe:
                                idx = pe['startIndex']
                                print(f'R{ri}C{ci}: insertText at {idx}')
```

For a fresh 11×2 table, the cell indices follow a predictable pattern (incrementing by 2–5 per cell). The text-start index is where the initial `\n` lives — you insert text AT this index to place it before the newline.

## Step 3 — Populate Cells: CRITICAL: HIGHEST index FIRST

**This is the most important rule.** When inserting text into table cells via a single `batchUpdate`, you MUST order `insertText` requests from HIGHEST index to LOWEST.

Why: Each `insertText` shifts ALL subsequent indices forward by the length of the inserted text. If you insert starting from row 0, every later request's index reference becomes stale because the document has shifted beneath it.

**✅ Correct order:** R10 → R9 → R8 → ... → R0 (descending by index)

```python
requests = []

# Row 10 (highest index) — insert first in the array
requests.append({
    'insertText': {
        'text': 'Mrs. Priyanka Loya\n\nSignature: _________________',
        'location': {'index': 17709}
    }
})
# Row 9
requests.append({
    'insertText': {
        'text': 'Mr. Manoj Kumar Pandey\n\nSignature: _________________',
        'location': {'index': 17704}
    }
})
# ... continue downward ...
# Row 0 (header — lowest index) — insert last in the array
requests.append({
    'insertText': {
        'text': 'MORTGAGEES',
        'location': {'index': 17659}
    }
})
requests.append({
    'insertText': {
        'text': 'MORTGAGOR',
        'location': {'index': 17657}
    }
})

# Execute in one batch
result = docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': requests}
).execute()
```

**❌ Wrong order:** R0 → R1 → R2 (ascending by index) — every insert shifts all subsequent cell targets, causing all text to pile into the first cell.

## Step 4 — Apply Formatting

After all text is inserted, apply formatting using the final (shifted) indices. Read the doc again to get accurate positions:

```python
doc = docs.documents().get(documentId=doc_id).execute()
# Find the table and get start/end indices from textRuns

requests = [
    # Bold + font size for header
    {
        'updateTextStyle': {
            'range': {'startIndex': 17657, 'endIndex': 17679},
            'textStyle': {
                'bold': True,
                'fontSize': {'magnitude': 9, 'unit': 'PT'}
            },
            'fields': 'bold,fontSize'
        }
    },
    # Font size for all table content
    {
        'updateTextStyle': {
            'range': {'startIndex': 17681, 'endIndex': 18450},
            'textStyle': {
                'fontSize': {'magnitude': 9, 'unit': 'PT'}
            },
            'fields': 'fontSize'
        }
    },
]

result = docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': requests}
).execute()
```

**⚠️ Font size must be a Dimension object**, not a number:
- ✅ Correct: `'fontSize': {'magnitude': 9, 'unit': 'PT'}`
- ❌ Wrong: `'fontSize': 9` — raises `HttpError 400: Invalid value`

## Step 5 — Delete a Table (to start over)

If the table content is corrupted (all text landed in one cell due to wrong index order), delete the table and re-create:

```python
# Find the table start/end indices first
# Then delete the full range
requests = [{
    'deleteContentRange': {
        'range': {
            'startIndex': 17654,  # table start
            'endIndex': 18451     # table end + 1
        }
    }
}]
```

## Full Verified Example (Jun 2026 — Deed of Cancellation)

This was used to create a 2-column, 11-row table in a Google Doc. The table listed MORTGAGOR entities (left column) and MORTGAGEES with signature spaces (right column):

| Row | Left (Mortgagor) | Right (Mortgagees) |
|-----|------------------|-------------------|
| 0 | **MORTGAGOR** (header) | **MORTGAGEES** (header) |
| 1 | SEVAGANAPALLI LAND PARTNERS (through Nishant Ranka) | Mr. Sudharsan JP + signature |
| 2 | (empty — merged visually) | Mrs. Prathyusha Vuppala + signature |
| 3 | (empty) | Mrs. Mamidibathula Deepthi + signature |
| 4 | (empty) | Mr. Bhagavan Krishna Paduchuri + signature |
| 5 | M/s DRA REALTY PRIVATE LIMITED (through Nishant Ranka) | Mr. Ajay Singh Bist + signature |
| 6 | (empty) | Mrs. Mummidi Lakshmi Sahitya + signature |
| 7 | (empty) | Mr. G Kiran Kumar + signature |
| 8 | (empty) | Mrs. Silpa Naidu Chirumavilla + signature |
| 9 | (empty) | Mr. Manoj Kumar Pandey + signature |
| 10 | (empty) | Mrs. Priyanka Loya + signature |

Cell indices for a fresh 11×2 table are: R0C0=17657, R0C1=17659, R1C0=17662, R1C1=17664, R2C0=17667, R2C1=17669, ... (incrementing by 5 for each pair, then by 3 for the next row start).

## Pitfalls

- **Index drift is cumulative** — inserting 50 chars of text at index 17657 shifts ALL subsequent cell references by +50. If you then reference R5C1 at its original index 17684, you're actually writing into R1C1. Always order from highest index to lowest.
- **Formatting after insertText** — after all insertText calls, the indices have shifted. Read the document fresh to get accurate positions before applying formatting.
- **Font size requires Dimension object** — `{'magnitude': N, 'unit': 'PT'}` not a bare integer.
- **No mergeCells via API** — the Google Docs API does not support `mergeTableCells`. To create visually merged cells, leave extra cells empty and use empty-text placeholders.
- **DeleteContentRange must be exact** — use table startIndex and endIndex (not guessed values). End index is exclusive (endIndex + 1 range if inclusive).
- **Paragraph with inline image** — if the table replaces a photo, delete the image's inlineObjectElement range first (startIndex to endIndex, typically 1 char), then insertTable at the same index.
- **The Google Docs API processes requests in array order** — it does NOT reorder or batch by type. Each request sees the cumulative state from all previous requests in the array. This is why insert order matters so much.
