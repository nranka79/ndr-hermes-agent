# Google Docs API — Table Manipulation

Inserting and populating tables via the Docs API requires careful index management. The key rule: **insert text from HIGHEST cell index to LOWEST cell index** to avoid cascade shifts.

## Inserting a Table

```python
docs = build_service('docs', 'v1')
requests = [{
    'insertTable': {
        'rows': 11,       # header row + data rows
        'columns': 2,
        'location': {'index': INSERTION_INDEX}
    }
}]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

The table is inserted at the given index, shifting existing content after it.

## Adding Columns to an Existing Table

Use `insertTableColumn` to add a column to the right of a specified column. Critical: **column inserts shift the startIndex of every subsequent table** in the document. Unlike text inserts (which can be done in descending order in one batch), column inserts must be done **one at a time, re-fetching the document between each**.

### Single column insert

```python
requests = [{
    'insertTableColumn': {
        'tableCellLocation': {
            'tableStartLocation': {'index': TABLE_START_INDEX},
            'rowIndex': 0,
            'columnIndex': LAST_COL_INDEX  # 0-indexed, N-1 for an N-col table
        },
        'insertRight': True   # inserts AFTER the specified column
    }
}]
docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': requests}).execute()
```

### Multi-table column inserts (sequential, re-fetch each time)

When adding columns to multiple tables in the same document, each `insertTableColumn` shifts subsequent tables' `startIndex`. You **cannot** batch them — do them one at a time:

```python
# 1. Insert column in Table A
docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': [req_a]}).execute()

# 2. Re-fetch the doc to get Table B's new startIndex
doc = docs.documents().get(documentId=DOC_ID).execute()
# locate Table B's startIndex from updated content...

# 3. Insert column in Table B using the new startIndex
docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': [req_b]}).execute()

# 4. Repeat for Table C...
```

After all columns are inserted, fetch the document once to get the cell content `startIndex` values for the new (empty) cells, then batch-insert text in descending index order as usual.

### Filling new column cells (text + styling)

Newly inserted column cells contain a single `\n` character. Insert text at that cell's `startIndex` (before the newline), then style it:

```python
requests = [
    # Insert text
    {'insertText': {'location': {'index': CELL_START_INDEX}, 'text': '755.24'}},
    # Style red
    {'updateTextStyle': {
        'range': {'startIndex': CELL_START_INDEX, 'endIndex': CELL_START_INDEX + 6},
        'textStyle': {'foregroundColor': {'color': {'rgbColor': {'red': 1.0, 'green': 0.0, 'blue': 0.0}}}},
        'fields': 'foregroundColor'
    }}
]
```

Unlike column inserts, text inserts across multiple cells **can** be batched in one call — just track the cumulative shift as each insert adds its text length. Use a running `shift` variable to adjust subsequent cell indices within the same batch.

## Finding Cell Indices After Insertion

After inserting the table, fetch the document to discover each cell's content start index:

```python
doc = docs.documents().get(documentId=doc_id).execute()
for elem in doc['body']['content']:
    if 'table' in elem:
        for ri, row in enumerate(elem['table']['tableRows']):
            for ci, cell in enumerate(row['tableCells']):
                for ce in cell.get('content', []):
                    if 'paragraph' in ce:
                        for pe in ce['paragraph'].get('elements', []):
                            if 'textRun' in pe:
                                cell_idx = pe['startIndex']  # insert text here
```

Each empty cell contains a single `\n` at its `startIndex`. Inserting at that index adds text before the newline.

**CRITICAL: textRun startIndex = cell_startIndex + 1.** The cell's structural marker occupies `cell_startIndex`, so the first textRun (even if empty, containing just `\n`) is always at `cell_startIndex + 1`. When populating, always insert at `cell_startIndex + 1`, not at `cell_startIndex`. Inserting at `cell_startIndex` puts text outside the paragraph and raises `"The insertion index must be inside the bounds of an existing paragraph"`.

### Inserting Into Empty Cells: Never deleteContentRange

Empty table cells (just created by `insertTable`) contain a single paragraph with one textRun containing `\n`. **Do NOT use `deleteContentRange` on this content** — the API returns `"Invalid deletion range"` because deleting the only content in a cell is structurally forbidden.

**CORRECT — insertText only (text prepends before `\n`):**
```python
# Cell at [cell_start, cell_end], textRun at [cell_start+1, cell_end] with content '\n'
{'insertText': {'location': {'index': cell_start + 1}, 'text': 'My cell content'}}
```
Result: `"My cell content\n"` — the original `\n` serves as the trailing newline.

**WRONG — deleteContentRange then insertText:**
```python
# This fails with 400 error:
{'deleteContentRange': {'range': {'startIndex': cell_start+1, 'endIndex': cell_end}}}
{'insertText': {'location': {'index': cell_start+1}, 'text': 'My cell content\n'}}
```

### Large-Table Strategy: One Row at a Time (Re-fetch Between Rows)

For tables with many rows (16+), batch insertion of 60+ cells in a single `batchUpdate` fails because each `insertText` shifts subsequent indices and the API processes requests sequentially against fixed-at-submission indices. The cumulative shift approach (below) works for moderate batches but becomes unreliable past ~40 insertions.

**Most reliable strategy for large tables: process one row at a time, fetching the document between rows.**

```python
data = [('Item', 'Survey', 'Extent'), ('1', '181', '3 Ac'), ...]  # 16 rows

for r in range(len(data)-1, -1, -1):  # bottom row first
    # 1. Fetch current doc to get fresh cell indices for this row
    doc = docs_svc.documents().get(documentId=DOC_ID).execute()
    # Find the table and extract current row's cell startIndices
    table_num = 0
    row_cell_starts = None
    for item in doc['body']['content']:
        if 'table' in item:
            if table_num == TARGET_TABLE:
                cells = item['table']['tableRows'][r]['tableCells']
                row_cell_starts = [c['startIndex'] for c in cells]
                break
            table_num += 1

    # 2. Insert into cells right-to-left within this row
    for c in range(len(row_cell_starts)-1, -1, -1):
        cs = row_cell_starts[c]         # cell startIndex
        text = data[r][c]
        req = [{'insertText': {'location': {'index': cs+1}, 'text': text}}]
        if r == 0:  # bold header
            req.append({'updateTextStyle': {
                'range': {'startIndex': cs+1, 'endIndex': cs+1+len(text)+1},
                'textStyle': {'bold': True}, 'fields': 'bold'
            }})
        docs_svc.documents().batchUpdate(documentId=DOC_ID, body={'requests': req}).execute()
```

Slower (one re-fetch per row + one batch per cell) but 100% reliable. The re-fetch between rows ensures indices are correct even after previous rows' text shifted the document.

## Critical: Insert Text in DESCENDING Index Order

Every `insertText` shifts all subsequent indices forward by the length of the inserted text. **If you insert in ascending index order, your second insert targets a shifted index and lands in the wrong cell.**

**CORRECT — descending index order (highest first):**

```python
# Build list of (cell_index, text_content) pairs
cells = [
    (17709, 'Row 10, Cell 1 text'),   # highest index
    (17707, 'Row 10, Cell 0 text'),
    (17704, 'Row 9, Cell 1 text'),
    ...
    (17659, 'Row 0, Cell 1 text'),    # header
    (17657, 'Row 0, Cell 0 text'),    # lowest index — processed last
]

requests = [{'insertText': {'text': text, 'location': {'index': idx}}}
            for idx, text in cells]   # already in descending order

docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

**WRONG — ascending order causes index drift and text piles up in one cell.**

### Multi-table batch inserts: cumulative shift approach

When inserting text across cells from multiple tables (e.g., populating a new column across 3 tables with 40+ cells total), the cells' `startIndex` values come from different document regions and descending-order sorting alone is not sufficient — the real challenge is that every insert shifts the absolute index of every subsequent cell in the batch, even those in completely different tables.

Use a **running cumulative shift counter** to compute each cell's effective index in the request array, processing tables in document order:

```python
requests = []
shift = 0

def add_text_requests(cell_indices, values):
    global shift
    for ri in range(len(cell_indices)):
        adj_idx = cell_indices[ri] + shift
        val = str(values[ri])
        # Insert text
        requests.append({
            'insertText': {
                'location': {'index': adj_idx},
                'text': val
            }
        })
        # Style
        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': adj_idx,
                    'endIndex': adj_idx + len(val)
                },
                'textStyle': {'foregroundColor': ...},
                'fields': 'foregroundColor'
            }
        })
        shift += len(val)

# Process tables in document order
add_text_requests(table1_indices, table1_values)
add_text_requests(table2_indices, table2_values)
add_text_requests(table3_indices, table3_values)

# Execute in batches of 50
for batch_start in range(0, len(requests), 50):
    batch = requests[batch_start:batch_start + 50]
    docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': batch}).execute()
```

This works because:
- Each table's cells are processed in document order (row 0 → row N, table 1 → table 2 → table 3)
- The `shift` variable accounts for every `insertText` that came before
- Unlike sorting by raw index, this handles `insertText + updateTextStyle` pairs (two requests per cell) and works across discontinuous index ranges
- The `updateTextStyle` requests don't shift indices (they style in-place), so they don't affect `shift`

**Why not just sort by descending index?** When cells come from multiple tables across the document, their startIndex values may not be monotonically related to the insertion order you want (you typically process tables in document order, but cells within one table might have higher raw indices than cells in later tables). The cumulative shift approach is simpler: process cells in your natural order (document order, row by row), and let the shift counter handle the maths.

## Finding Inline Objects (Images) for Replacement

To replace an image with a table, first locate the inline object:

```python
doc = docs.documents().get(documentId=doc_id).execute()
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        for pe in elem['paragraph'].get('elements', []):
            if 'inlineObjectElement' in pe:
                obj = pe['inlineObjectElement']
                img_start = pe['startIndex']
                img_end = pe['endIndex']
                print(f'Image at {img_start}-{img_end}, id={obj["inlineObjectId"]}')
```

Delete the image, then insert the table at the same index:

```python
requests = [
    {'deleteContentRange': {
        'range': {'startIndex': img_start, 'endIndex': img_end}
    }},
    {'insertTable': {
        'rows': 11, 'columns': 2,
        'location': {'index': img_start}
    }}
]
```

## Formatting Table Content

### Font size must be a Dimension object

```python
# CORRECT:
{'fontSize': {'magnitude': 9, 'unit': 'PT'}}

# WRONG — will return HTTP 400:
{'fontSize': 9}
```

### Style update example

```python
requests.append({
    'updateTextStyle': {
        'range': {'startIndex': N, 'endIndex': M},
        'textStyle': {
            'bold': True,
            'fontSize': {'magnitude': 9, 'unit': 'PT'}
        },
        'fields': 'bold,fontSize'
    }
})
```

## Editing Existing (Non-Empty) Cell Content

When a table cell already has placeholder content (underlines, checkbox characters, pre-filled text), you must **delete the old content** before inserting new text. This is fundamentally different from populating empty cells (which only need `insertText`).

### The cell +1 off-by-one rule

**Whether the cell is empty or filled, the textRun's `startIndex` is always `cell_startIndex + 1`.** The cell's structural boundary marker occupies `cell_startIndex`, so the first textRun begins at `cell_startIndex + 1`.

```python
# When reading cell structure:
#   cell['startIndex'] = 1525
#   textRun['startIndex'] = 1526   (= 1525 + 1)
#   textRun['endIndex'] = 1553
#   content = '__________________________\n'
```

When deleting content, target the **textRun indices** (not the raw cell indices):

### Pattern: delete + insert in one batch update

Works when the cell has content with a trailing `\n` (most cells):

```python
# Cell at [1525, 1580] with textRun at [1526, 1553]: '__________________________\n'
# Delete the underscores (keeping the \n), insert new text

requests = [
    # Delete only the placeholder content, not the trailing \n
    {'deleteContentRange': {'range': {'startIndex': 1526, 'endIndex': 1552}}},
    # Insert replacement at the same position
    {'insertText': {'location': {'index': 1526}, 'text': 'B-27, Zonasha Paradise, Bengaluru'}}
]
```

**Key rules:**
- Keep the trailing `\n` — don't deleteContentRange through it (API rejects deleting paragraph boundaries)
- Process **highest index first** when doing multiple delete+insert pairs in one batch
- After the first delete+insert in a batch, subsequent textRun indices shift — account for this

### Pattern: delete paragraph content separately (multi-paragraph cells)

When a cell contains multiple paragraphs (e.g., two lines of underlines), you **cannot** deleteContentRange across the paragraph boundary in one operation. Delete each paragraph's text content separately:

```python
# Address cell with 2 paragraphs:
#   Paragraph 0: (1526, 1553) '__________________________\n'
#   Paragraph 1: (1553, 1580) '__________________________\n'

# Step 1: Delete paragraph 1's content (higher index first)
{'deleteContentRange': {'range': {'startIndex': 1553, 'endIndex': 1579}}}
# Step 2: Re-fetch doc to get shifted indices
# Step 3: Delete paragraph 0's content (now at shifted indices)
{'deleteContentRange': {'range': {'startIndex': 1526, 'endIndex': 1527}}}  # just the '\n' leftover
# Step 4: Insert new text
{'insertText': {'location': {'index': 1526}, 'text': 'B-27, Zonasha Paradise, Bengaluru\n'}}
```

**Alternative (simpler):** Re-fetch the document between each delete+insert pair and work with fresh indices. Three separate `batchUpdate` calls with re-fetching is more reliable than trying to track index shifts within one batch.

### Pattern: replaceAllText for unique cell strings

When a cell contains a unique-enough string that won't appear elsewhere in the document, skip index arithmetic entirely:

```python
{'replaceAllText': {
    'containsText': {'text': 'S/o __________________', 'matchCase': True},
    'replaceText': 'S/o Mr. Ram Kumar'
}}
```

**Caveats:**
- `matchCase: False` makes it case-insensitive — use `True` for precision
- Replaces ALL occurrences document-wide — verify uniqueness first
- After replacement, the cell text is clean. No index arithmetic needed.
- Works across paragraph boundaries automatically (one of the few operations that does)

### Pattern: checkbox character replacement

Checkboxes in Google Docs are Unicode characters:
- ☐ = U+2610 (unchecked)
- ☑ = U+2611 (checked)

They appear as a single character in a textRun, followed by `\n`:

```python
# Cell[2,2] at (786, 789): textRun (787, 789) = '☐\n'
# Replace ☐ → ☑

requests = [
    # Delete the checkbox character only (1 char), keep the \n
    {'deleteContentRange': {'range': {'startIndex': 787, 'endIndex': 788}}},
    # Insert checked version
    {'insertText': {'location': {'index': 787}, 'text': '☑'}}
]
```

**Key detail:** The checkbox character is at `textRun['startIndex']`, not `cell['startIndex']`. Always read the textRun boundaries, not the cell boundaries.

### Pitfalls for editing existing content

- **Do NOT deleteContentRange on just the cell's structural boundary** — `deleteContentRange` at `cell['startIndex']` (without the +1) raises `"Invalid deletion range"` because it tries to delete the structural marker.
- **Do NOT deleteContentRange across paragraph boundaries** — each paragraph inside a cell must be edited separately. The error message is `"Invalid deletion range. Cannot delete the requested range."`
- **After any delete+insert, the cell's textRun indices shift** — if you need to edit another cell in the same table after the first edit, re-fetch the document for fresh indices rather than trying to calculate the offset.
- **`replaceAllText` is document-wide** — always search the document text first to confirm the string is unique before using it for table cell editing.
- **GWS rate limit (60 write ops/min)** — when editing many cells individually, batch adjacent operations into a single `batchUpdate` call where possible to stay under quota.

### Full worked example: Filling Form 2 partnership reconstitution

See `references/docs-api-form-2-fill.md` for the complete end-to-end workflow of filling this legal form (checkboxes + partner details + address/age fields) using all of the above patterns.

## Refs (for gws-automation umbrella)

The gws-automation umbrella also references:
- `references/drive-file-upload.md` — Drive file upload with DRAAS naming conventions

(This note is in docs-api-tables.md solely as a cross-reference pointer so future agents discover the file-upload reference when working with Drive API operations.)

## Fixing Corrupted Cells with replaceAllText

When `insertText` is applied to a cell that already has content (from a previous partial insert or failed batch), the new text **prepends** before the old text instead of replacing it. This produces concatenated garbage like `"AY 2025-26AY 2022-23\n"`.

**Don't try to delete and re-insert** — the index management is fragile when content length is unpredictable. Instead, use `replaceAllText` which does a global find-and-replace across the entire document with no index arithmetic:

```python
corrupted = 'AY 2025-26AY 2022-23'  # the exact current text in the cell
replacement = 'AY 2025-26'

docs_svc.documents().batchUpdate(documentId=DOC_ID, body={'requests': [{
    'replaceAllText': {
        'containsText': {'text': corrupted, 'matchCase': False},
        'replaceText': replacement
    }
}]}).execute()
```

**Caveats:**
- `replaceAllText` is **case-insensitive** when `matchCase: False` — ensure your search string won't match other document text
- It replaces ALL occurrences across the entire document, not just in the target cell. Use a sufficiently unique substring to avoid side effects
- After replacement, the cell text is clean and ready for further `insertText` if needed
- This is a **one-shot fix** — use it to clean up after a failed batch, not as a primary population strategy

## insertTable Reply: Getting the New Table's startIndex

When you call `insertTable` in a `batchUpdate`, the reply contains the new table's `startIndex`. Use this to predict cell locations without an extra document fetch:

```python
result = docs_svc.documents().batchUpdate(documentId=DOC_ID, body={'requests': [{
    'insertTable': {'rows': 9, 'columns': 5, 'location': {'index': SOME_INDEX}}
}]}).execute()

table_start = result['replies'][0]['insertTable']['startIndex']
print(f'Table starts at {table_start}')
# Cell (0,0) will be at table_start + 2
```

However, for correctness-sensitive operations (especially with multiple tables), still prefer re-fetching the document — the structural overhead between tables can vary.

## Pitfalls

- **Column inserts must be done sequentially** — `insertTableColumn` shifts the startIndex of every later table. You cannot batch column inserts for different tables in one call. Re-fetch the doc between each column insert to get correct startIndex values.
- **Index cascade is the #1 failure mode** — always insert text from highest index to lowest. Re-read the doc to confirm indices before each batch if you're doing multi-step population.
- **Deleting content shifts indices** — after deleting an image or text, the indices of everything after the deletion decrease by the deleted length. Account for this when inserting a replacement at the same position.
- **Font size must be a Dimension dict**, not a plain number. The API silently rejects malformed Dimension values with a 400 error on that specific request.
- **batchUpdate is atomic per call** — if one request in a batch fails, all requests in that batch are rolled back. Test formatting requests separately from insert requests.
- **Table cell ranges after insertion** — cell indices are stable once the table exists. Read them once, then batch all insertText requests in descending order.
- **No native cell merge via API** — the Docs API does not support `mergeTableCells`. To simulate merged cells, leave target cells empty and put content only in the first cell of the span.
- **Column widths cannot be set via API** — accept the default equal-width columns, or resize manually after creation.
- **Do NOT deleteContentRange on the only content in a cell** — empty cells contain a single `\n` in a textRun. Attempting to `deleteContentRange` this content returns a 400 error. Use `insertText` at `cell_startIndex + 1` instead.
- **"Insertion index must be inside bounds of an existing paragraph"** means your insert index is at a structural boundary. Always insert at `cell_startIndex + 1`, never at `cell_startIndex`.
- **Large-table batches fail past ~40 cells** — even with proper R2L ordering, batches of 60+ insertText operations fail with index-out-of-bounds errors. Use one-row-at-a-time strategy with re-fetch between rows.
- **Multi-table population** — process one table at a time, re-fetching the document between tables, or use the cumulative shift counter approach for moderate batches.
- **Google Docs API rate limit: 60 write requests per minute per user** — Each `batchUpdate` call counts as one write request. If you process cells one-at-a-time with individual `batchUpdate` calls, you'll exhaust the quota in ~60 seconds. Mitigations: batch operations where possible, insert `time.sleep(1)` between calls if processing one-at-a-time, and process cells right-to-left within each table to batch more operations per call.
- **Rate limit recovery** — When hitting `Quota exceeded for quota metric 'Quota group for write operations'` (HTTP 429), wait **70+ seconds** then retry. The quota resets on a per-minute sliding window. Do NOT retry immediately — that wastes the one operation that did succeed and burns more quota on the same failed batch.
- **Avoid inserting unnecessary blank paragraphs** — If the area where you need to insert a table doesn't have a blank paragraph, insert the table at the **start index of the paragraph immediately after** the section heading, not at the end index of the heading. The `insertTable` location must be inside an existing paragraph, not at its boundary.
- **When insertion point IS at a paragraph boundary** (e.g., right after a section heading with no blank line between), insert a blank paragraph first: `{'insertText': {'location': {'index': heading_end}, 'text': '\n'}}`. Then insert the table inside the new blank paragraph.

## Converting Pipe-Markdown Tables to Real Tables

The Google Docs API does not auto-convert markdown pipe tables (`| A | B |`) into real tables. You must delete the pipe paragraphs and insert proper table elements.

### Full workflow

```
1. Identify all pipe table paragraph ranges in the document
   (each pipe table row is a separate paragraph starting with '|')

2. Delete all pipe table paragraphs in a single batch (right-to-left by index)

3. For each location where a table should appear:
   a. If the area after the section heading has no blank paragraph,
      insert one: insertText '\n' at heading_endIndex
   b. Fetch the document to find the blank paragraph's startIndex
   c. Insert the table at that blank paragraph's startIndex:
      {'insertTable': {'rows': N, 'columns': M, 'location': {'index': blank_start}}}

4. Fetch the document to get cell startIndex values for the new table

5. Populate cells using insertText at (cell_startIndex + 1), processed
   right-to-left within the table. For large tables (16+ rows), process
   one row at a time, re-fetching the document between rows.
```

### Deleting the right range

Pipe paragraphs include the final `\n`. A pipe paragraph at `[S-E]` with content `'| A | B |\n'` should be deleted as `deleteContentRange [S, E]` (endIndex is exclusive). Include any blank paragraph after the pipe table in the deletion range to prevent extra whitespace.

### Multiple duplicate tables

The `insertTable` call creates an empty table. If you accidentally insert into a blank area that has multiple blank lines, you may get **duplicate tables** (one per blank line). Detect this by fetching the document and checking for consecutive tables with the same row/column dimensions. Delete the extras (keeping the first one) using `deleteContentRange [table_start, table_end]`, processed right-to-left.

### Cell index prediction vs re-fetch

After table insertion, cell startIndex follows a predictable pattern:
```
For a C-column table with 2-index cells (each cell = 2 indices):
  Row 0 cell 0 startIndex = table_startIndex + 2
  Row 0 cell c startIndex = table_startIndex + 2 + c * 2
  Row r cell c startIndex = table_startIndex + 2 + r * (2*C + 1) + c * 2
```
Where `(2*C + 1)` is the row stride (e.g., 9 for 4-col tables, 11 for 5-col, 13 for 6-col).

**However, always re-fetch the document to get actual cell indices** — the formula is fragile and breaks if any structural elements (blank paragraphs, other tables) exist near the insertion point. The re-fetch is the reliable source of truth.
