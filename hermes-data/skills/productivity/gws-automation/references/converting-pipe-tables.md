# Converting Pipe-Markdown Tables to Proper Google Docs Tables

Documents containing pipe tables (`| Header | Data |`) as plain-text paragraphs need conversion to real Docs tables for professional formatting. This reference covers the complete workflow.

## Overview

Pipe tables appear as consecutive paragraphs starting with `|`. Converting them involves:

1. Identify all pipe table groups in the document
2. Delete the pipe paragraphs in a single batch (R2L)
3. Insert proper Docs tables at the vacated positions
4. Populate each table's cells with the original data

## Step 1: Identify pipe table groups

```python
doc = docs_service.documents().get(documentId=doc_id).execute()
pipe_groups = []  # (start, end, row_count, col_count, data_rows)

for item in doc['body']['content']:
    para = item.get('paragraph')
    if para:
        text = ''.join(e.get('textRun', {}).get('content', '')
                      for e in para.get('elements', []))
        if text.startswith('|'):
            # Parse columns from header
            cols = [c.strip() for c in text.split('|')[1:-1]]
            # Accumulate group...
```

The blank line after the last pipe row is typically at `[last_pipe_end, last_pipe_end+1]`.

## Step 2: Delete pipe paragraphs in one batch

Process RIGHT-TO-LEFT (highest index first) so lower-indexed deletions stay valid:

```python
requests = []
for start, end, _, _, _ in sorted(pipe_groups, key=lambda x: x[0], reverse=True):
    # Include the trailing blank line
    requests.append({
        'deleteContentRange': {'range': {'startIndex': start, 'endIndex': end}}
    })

docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

## Step 3: Insert proper tables

After deletions, fetch the document to find blank paragraphs where tables should go. Insert tables inside blank paragraphs (not at paragraph boundaries):

```python
doc = docs_service.documents().get(documentId=doc_id).execute()
# Find blank paragraphs near section headings...

insert_reqs = []
for pos in sorted(insertion_positions, reverse=True):
    insert_reqs.append({
        'insertTable': {
            'rows': rows,
            'columns': cols,
            'location': {'index': pos}
        }
    })

docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': insert_reqs}).execute()
```

**Critical:** The insertion index must be INSIDE a paragraph (not at its boundary). If no blank paragraph exists at the right position, insert `\n` at the heading's end index first to create one, then insert the table at the same position.

## Step 4: Populate cells

Fetch the document to get cell `startIndex` values for each new table. Each cell occupies 2 index positions (`[start, start+2]`), with the textRun at `start+1`. Populate cells by inserting text at `start+1` — do NOT use `deleteContentRange` on empty cells.

Process one table at a time, re-fetching between tables due to index shifts. Within each table, process rows bottom-up and cells right-to-left.

See `docs-api-tables.md` for detailed population strategies and the one-row-at-a-time approach for large tables.

## Handling duplicate tables

If multiple blank paragraphs exist at the insertion point (e.g., from accidentally inserting extra `\n`), multiple tables may be created. Delete the extras by their `[startIndex-endIndex]` range, keeping only the first table in each section. Process deletions right-to-left.

## Alternative approach: Insert table first, then delete pipes

The delete-first approach works but requires finding blank paragraphs post-deletion. A simpler approach is to insert the table at the pipe text's position first.

### Steps

1. **Find the startIndex of the first pipe paragraph** — this is your insertion point.
2. **Create the table** at that index:
   ```python
   docs.documents().batchUpdate(documentId=doc_id, body={'requests': [{
       'insertTable': {'rows': num_rows, 'columns': num_cols,
                       'location': {'index': insert_index}}
   }]}).execute()
   ```
   The table pushes content down; pipe paragraphs end up AFTER the table.
3. **Re-fetch the document** to get the new table's cell indices.
4. **Populate cells** — each empty cell has a newline at cell_start+1. Insert text there:
   ```python
   {'insertText': {'location': {'index': cell_start + 1}, 'text': cell_text}}
   ```
5. **Apply text styling** via `updateTextStyle` (bold for header, font size, font family).
6. **Delete the old pipe paragraphs** — scan for paragraphs starting with `|`, delete right-to-left.
7. **Repeat** for each table, re-fetching between iterations.

### Advantages over delete-first
- No hunting for blank paragraphs — you insert at a known index
- Pipe text is in a predictable location (after the table)
- Works even when there's no blank line between pipe text and surrounding content

## Table cell background limitation

After creating a table via `insertTable`, `updateTableCellStyle` with `tableCellLocation.rowIndex` may fail:
```
Invalid requests[N].updateTableCellStyle: The rowSpan must be strictly positive, was: 0
```
This occurs on newly created tables. **Workaround:** Use `updateTextStyle` for bold/font (these work). Skip `updateTableCellStyle` for background colors. Apply header shading manually in-browser if critical.

- **Too many blank paragraphs** — inserting `\n` creates a new paragraph. One `\n` is enough; inserting multiple creates extras that can cause duplicate tables.
- **Rate limit** — Google Docs API allows 60 write requests per minute per user. Batch as many operations as possible into one `batchUpdate` call.
- **Large tables (16+ rows)** — populating all cells in one batch fails due to index cascade. Use the one-row-at-a-time strategy instead.
- **Adjacent tables** — if two pipe tables are adjacent (e.g., Section 1 and Section 2 tables), deleting both and inserting both requires careful index management. Process deletions and insertions right-to-left.
