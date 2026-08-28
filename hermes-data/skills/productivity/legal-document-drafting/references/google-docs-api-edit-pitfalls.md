# Google Docs API — Edit Pitfalls That Cause Document Corruption

**Trigger:** When using `gws_skill_bridge.call("docs_get", ...)` or `build_service("docs", "v1")` to **edit an existing Google Doc** (paragraph rewrites, color changes, numbering fixes) — not when creating new docs from scratch.

## Two Gotchas That Can Wreck a Document (Jul 2026)

The Millers Road lease deed was heavily corrupted during a major edit round. Recovery took 50+ targeted `deleteContentRange` + `insertText` calls to restore. Both bugs were caused by the same root issue: **treating text-content indices as document indices**.

### Gotcha #1: text-content indices ≠ document indices

When you extract text from a Google Doc by walking all `textRun` elements and concatenating their `content` strings, you get a "text-content" index. **This is NOT the same as the document's character index used in `batchUpdate` operations.**

Why? The document index includes characters you can't see in the extracted text:

- **Paragraph break characters** — every paragraph (except the last in a section) has a trailing `\n` represented as a separator in the document index
- **Section break characters** — `\n` between sections
- **Table cell boundary characters**
- **Other block-level separators**

**Example:** If you extract text and find "Miller's Road" at position 72, the actual document index for the apostrophe character might be 77 — there's a 5-character gap for paragraph break(s) in between.

**What this breaks:** When you call `deleteContentRange({"startIndex": 72, "endIndex": 78})` using a text-content index, you don't delete "Miller'" — you delete some random 6 characters from the wrong position in the document, often corrupting "L E S S E E" into "L E S S E" by deleting one of the E's.

**The fix:** Never use text-content indices. Either:
- Use `find_doc_range()` helper that walks the document structure to map text positions to document indices
- Or use `replaceAllText` for global text replacement (safer for small targeted changes)

```python
# BAD — uses text-content indices, causes corruption
full_text = get_all_text(doc)  # concatenates textRun contents
pos = full_text.find("Mille\u2019s Road")
docs.batchUpdate(doc_id, body={
    "requests": [{"deleteContentRange": {"range": {"startIndex": pos, "endIndex": pos+14}}}]
})

# GOOD — uses replaceAllText, no index math needed
docs.batchUpdate(doc_id, body={
    "requests": [{"replaceAllText": {
        "containsText": {"text": "Mille\u2019s Road"},
        "replaceText": "Miller\u2019s Road"
    }}]
})
```

**Limitation of `replaceAllText`:** it CANNOT apply text formatting (color, bold, etc.) to the replacement. So for "color this in blue" edits, you need the index-based approach — but you must do the index math correctly.

### Gotcha #2: paragraph.endIndex INCLUDES the trailing newline

When you read a paragraph's indices from the Docs API:
```python
block.get('startIndex')  # e.g. 7181
block.get('endIndex')    # e.g. 7332 — this INCLUDES the trailing \n
```

If you do `deleteContentRange({"startIndex": 7181, "endIndex": 7332})` to delete the paragraph and then `insertText({"location": {"index": 7181}, "text": "new paragraph text"})` WITHOUT including a trailing `\n` in your replacement, the next paragraph gets concatenated to the end of your new text. Result: two paragraphs merge into one.

**The fix:** Always include `\n` at the end of paragraph rewrites, OR be explicit about whether you're replacing the full paragraph (with newline) or just the text content (and you need to handle the newline separately).

```python
# BAD — paragraphs merge
new_text = "4. MONTHLY RENT\nIn consideration of the Lease..."  # MISSING \n at end
requests = [
    {"deleteContentRange": {"range": {"startIndex": p_start, "endIndex": p_end}}},
    {"insertText": {"location": {"index": p_start}, "text": new_text}},
]

# GOOD — newline preserved
new_text = "4. MONTHLY RENT\nIn consideration of the Lease...\n"  # has trailing \n
```

## Building a Safe Index Map

When you MUST do index-based edits (e.g. for color formatting), use this pattern:

```python
# Walk the document structure to build a precise (text_pos -> doc_idx) map
doc_index_map = []  # list of (doc_idx, char)

for block in doc.get('body', {}).get('content', []):
    if 'paragraph' in block:
        for elem in block['paragraph'].get('elements', []):
            if 'textRun' in elem:
                run_text = elem['textRun'].get('content', '')
                run_start_idx = elem.get('startIndex')
                for i, c in enumerate(run_text):
                    doc_index_map.append((run_start_idx + i, c))
    elif 'table' in block:
        # Tables have their own internal indices; include cell text
        for row in block['table'].get('tableRows', []):
            for cell in row.get('tableCells', []):
                for cell_block in cell.get('content', []):
                    if 'paragraph' in cell_block:
                        for elem in cell_block['paragraph'].get('elements', []):
                            if 'textRun' in elem:
                                run_text = elem['textRun'].get('content', '')
                                run_start_idx = elem.get('startIndex')
                                for i, c in enumerate(run_text):
                                    doc_index_map.append((run_start_idx + i, c))

# Helper to convert text-content position to document index
def text_pos_to_doc_idx(text_pos):
    if text_pos < 0 or text_pos >= len(doc_index_map):
        return None
    return doc_index_map[text_pos][0]

# Helper to find the doc-index range for a given string
def find_doc_range(text_to_find):
    full_text = ''.join(c for _, c in doc_index_map)
    pos = full_text.find(text_to_find)
    if pos < 0:
        return None
    doc_start = text_pos_to_doc_idx(pos)
    if pos + len(text_to_find) < len(full_text):
        doc_end = text_pos_to_doc_idx(pos + len(text_to_find))
    else:
        # End of document — use last textRun's endIndex
        last_end = None
        for block in doc.get('body', {}).get('content', []):
            if 'paragraph' in block:
                for elem in block['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        last_end = elem.get('endIndex', last_end)
        doc_end = last_end
    return doc_start, doc_end
```

## Safe Edit Pattern: Reverse-Order Edits Within a Single batchUpdate

If you need to make multiple `deleteContentRange + insertText` edits in one batch, **order them from highest to lowest document index**. This way, each edit doesn't shift the indices of the ones before it.

```python
# Collect all (doc_start, doc_end, old_text, new_text) tuples
edits = []
for old, new in fixes:
    rng = find_doc_range(old)
    if rng:
        edits.append((rng[0], rng[1], old, new))

# Sort by doc_start DESCENDING
edits.sort(key=lambda x: -x[0])

# Build requests in order
requests = []
for doc_start, doc_end, old, new in edits:
    requests.append({"deleteContentRange": {"range": {"startIndex": doc_start, "endIndex": doc_end}}})
    requests.append({"insertText": {"location": {"index": doc_start}, "text": new}})
    requests.append({"updateTextStyle": {
        "range": {"startIndex": doc_start, "endIndex": doc_start + len(new)},
        "textStyle": BLUE_TEXT_STYLE,
        "fields": "foregroundColor"
    }})

# Single batchUpdate — all operations apply to the document state at the START of the call
docs.batchUpdate(doc_id, body={"requests": requests}).execute()
```

**Within a single batchUpdate**, all requests see the original document state — so if you have multiple inserts in the same batch, you must use the original (pre-batch) indices. The reverse-order trick is for **separate** batchUpdate calls in sequence.

## Apostrophe + Curly-Quote Replacement Is a Quagmire

If you need to convert straight `'` apostrophes to curly `'` apostrophes throughout a document:

1. **`replaceAllText` with straight apostrophe is dangerous** — it can land mid-word and create artifacts like `Miller'`+`'`+`s` (i.e., `Miller''s` with both apostrophes).
2. **`deleteContentRange` + `insertText` per apostrophe requires precise index math** — using text-content indices corrupts the doc.
3. **Curly+straight artifacts (e.g., `’'`) often need a separate cleanup pass** — after replacement, re-walk the doc to find any `’'` patterns and delete the extra straight apostrophe.

**Safer approach:** If the document is a lease/contract with dozens of apostrophes, do it in three passes:
1. First pass: `replaceAllText` straight→curly (accept some artifacts)
2. Second pass: `deleteContentRange` for any known `’'` or `''` patterns (using the safe `find_doc_range()` helper)
3. Verify with a final read — count straight vs curly apostrophes and confirm zero `’'` artifacts

## The "Color Your Edits" Pattern (for Review Cycles)

When the user wants to see what changed in a draft (review/sign-off cycle), the convention is to color new/edited text. The user's color preference varies by document:

| Color | When to use | Code |
|-------|-------------|------|
| **RED** (`red: 1.0, green: 0.0, blue: 0.0`) | Default convention for legal doc redlines (per `references/document-editing-vs-new-creation.md`) | `RGB(1.0, 0.0, 0.0)` |
| **BLUE** (`red: 0.0, green: 0.0, blue: 0.9`) | User explicitly asked for blue (some review cycles — verify with the user) | `RGB(0.0, 0.0, 0.9)` |
| **PURPLE** (`red: 0.44, green: 0.19, blue: 0.63`) | Some original drafts use purple for "track changes" (e.g. v4 lease deed had purple markup) | `RGB(0.44, 0.19, 0.63)` |

**Always ask the user which color they want for the review cycle** if it's not explicit. Don't assume RED.

## Recovery: When the Doc Is Already Corrupted

If you discover a doc has been corrupted by a bad edit pass:

1. **Re-fetch the doc and walk every paragraph** — identify which paragraphs are corrupted vs clean
2. **For each corrupted span, find the corrupted text in the full text and use `find_doc_range()` to get the correct document indices**
3. **Do a single batchUpdate with all fixes, ordered highest-to-lowest doc index**
4. **Verify each fix landed correctly** by re-fetching and checking the affected paragraph

Recovery CAN be done — even from severe corruption. But it's 10x more work than doing the edits correctly the first time. Prefer `replaceAllText` for targeted text changes; reserve index-based edits for color formatting.

## The \"Highlight Changes\" Pattern (Background Color, Not Text Color)

When the user asks you to **highlight** edited text in a Google Doc (not change its color, but add a visual highlight like a yellow marker), use `updateTextStyle` with `backgroundColor`:

```python
requests = [{
    'updateTextStyle': {
        'range': {
            'startIndex': DOC_START_IDX,
            'endIndex': DOC_END_IDX
        },
        'textStyle': {
            'backgroundColor': {
                'color': {
                    'rgbColor': {
                        'red': 1.0,    # Yellow highlight
                        'green': 0.85,
                        'blue': 0.3
                    }
                }
            },
            'bold': True
        },
        'fields': 'backgroundColor,bold'
    }
}]
```

### Workflow

1. Read the current doc, build full text + position map by walking element startIndex/endIndex
2. Search for the exact edited text string in the concatenated full text
3. Walk the position map to find which textRun element contains the match, then compute doc_start_idx = element_startIdx + offset_within_element
4. Apply highlight via batchUpdate with updateTextStyle

### When to Use Highlight vs Text Color

| Technique | When to use |
|-----------|-------------|
| Text color (RED/BLUE) | Formal legal redline review cycles |
| Background highlight (Yellow) | User says "highlight this" or wants temporary visual marking |

### Pitfalls

- Do NOT highlight the entire text element — find the precise range of just the new text
- If you previously highlighted the whole element, first clear it (`backgroundColor: {}`, `bold: False`) then re-apply to just the target range
- Background colors survive document closed/reopen — they are not temporary annotations
- Combine with `bold: True` for maximum visibility

## Related References

- `references/document-editing-vs-new-creation.md` — RED vs BLACK convention for legal docs
- `references/surgical-edits-and-style-preferences.md` — don't make wider changes than requested
- `references/google-docs-api-table-coloring-limitation.md` — table cell text cannot be individually formatted
- `references/lease-draft-review-email-negotiation-trail.md` — full lease deed review workflow
