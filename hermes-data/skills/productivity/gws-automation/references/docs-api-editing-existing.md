# Google Docs API — Editing Existing Documents via batchUpdate

**See also:** `references/docs-api-formatting.md` for creating and formatting new docs, `references/docs-api-inspection-and-delivery.md` for inspection/duplication, `references/docs-api-tables.md` for table operations.

## Overview

When a user shares an existing Google Doc and asks you to update it — changing rates, dates, rewording clauses, adding new sections — the approach is:

1. **Copy the doc** via Drive API (never edit the original unless explicitly told)
2. Use `replaceAllText` for simple text substitutions
3. Use `deleteContentRange` + `insertText` for complex section rewrites/insertions
4. Apply operations **from the end of the document backwards** (highest index first)

## Step 1: Copy the Document

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')
source_id = 'ORIGINAL_DOC_ID'

copied = drive.files().copy(
    fileId=source_id,
    body={
        'name': 'New_Document_Name',
        'mimeType': 'application/vnd.google-apps.document'
    },
    fields='id, name, webViewLink'
).execute()

new_doc_id = copied['id']
print(f"Link: https://docs.google.com/document/d/{new_doc_id}/edit")
```

**Always share the copy link** with the user so they know where changes are happening.

## Step 2: Simple Text Replacements with replaceAllText

For straightforward string swaps (rates, dates, names) that appear the same everywhere in the document:

```python
docs = build_service('docs', 'v1')

requests = [
    {
        "replaceAllText": {
            "containsText": {
                "text": "17 June 2026",
                "matchCase": True  # optional — default False
            },
            "replaceText": "18 June 2026"
        }
    },
    {
        "replaceAllText": {
            "containsText": {"text": "TERM SHEET"},
            "replaceText": "BINDING TERM SHEET"
        }
    }
]

docs.documents().batchUpdate(
    documentId=new_doc_id,
    body={"requests": requests}
).execute()
```

**Why this works:** `replaceAllText` operates on content, not indices — no index calculation needed. Multiple replacements can be bundled in one `batchUpdate` call safely.

**Pitfall:** `replaceAllText` replaces EVERY occurrence. If the target string appears in multiple places (e.g. "Term Sheet" appears in both the title and body references), use `matchCase` and targeted strings to avoid over-replacement.

## Step 3: Complex Edits — replaceAllText Not Enough

When you need to rewrite entire sections, add new clauses, or delete+replace blocks of text:

### 3a. Read current indices

First, inspect the current document to find exact `startIndex`/`endIndex` of every paragraph:

```python
doc = docs.documents().get(documentId=doc_id).execute()

for elem in doc['body']['content']:
    start = elem.get('startIndex', '?')
    end = elem.get('endIndex', '?')
    if 'paragraph' in elem:
        text = ''.join(e.get('textRun', {}).get('content', '')
                       for e in elem['paragraph'].get('elements', []))
        if text.strip():
            print(f'[{start}-{end}] {text.rstrip()[:120]}')
    elif 'table' in elem:
        print(f'[{start}-{end}] [TABLE ({len(elem["table"]["tableRows"])} rows)]')
```

### 3b. Delete existing content + Insert new text

```python
# CRITICAL: The range [startIndex, endIndex) is exclusive of endIndex
# The LAST character of a paragraph element is always '\n' (the paragraph break)
# You CANNOT include this trailing '\n' in a deleteContentRange

# WRONG — will raise HttpError 400:
#   deleteContentRange: {"range": {"startIndex": 100, "endIndex": 150}}
#   where the paragraph ends with \n at [149-150]

# RIGHT — exclude the trailing \n:
#   deleteContentRange: {"range": {"startIndex": 100, "endIndex": 149}}
#   Then insert new text at position 100

docs.documents().batchUpdate(
    documentId=doc_id,
    body={"requests": [
        {
            "deleteContentRange": {
                "range": {"startIndex": 100, "endIndex": 149}  # without trailing \n
            }
        },
        {
            "insertText": {
                "location": {"index": 100},
                "text": "Replacement text here"
            }
        }
    ]}
).execute()
```

### 3c. Inserting new sections between existing ones

To add new paragraphs between two sections, insert at the **position right before the second section's heading**.

Example: add new content between Section 5 (ends at index 2186) and Section 6 (starts at index 2187):

```python
requests = [
    {
        "insertText": {
            "location": {"index": 2186},
            "text": "\n•  New bullet point here.\n\n•  Another new bullet here.\n\n"
        }
    }
]
```

## CRITICAL PITFALLS

### 0. Text-content positions are NOT document indices (Millers Road lease incident, 14 Jul 2026)

**The bug:** The `gws_skill_bridge.call("docs_get", ...)` wrapper returns a flattened `body` string by concatenating all `textRun.content` values. If you then search this flattened string for a substring and take its `find()` offset, **that offset is NOT a valid index for `deleteContentRange` or `insertText`**. Document indices count characters INCLUDING paragraph markers (`\n`), table cells (which contribute their own characters), section breaks, and other structural elements that are NOT in the flattened text.

**Concrete failure (real, this session):** A script tried to "remove 'by ' from 'in by their'" by finding "in by" in the flattened body and computing `deleteContentRange(start, start+3)`. But the flattened text skips over a table that contains 60+ characters of indexed content between positions where text appears contiguous. The `start` offset in the flattened string was 4525, but the actual document index was 5390 — a 865-character gap (one Schedule-A table cell). The delete landed inside a different paragraph, removing letters from unrelated words and creating "Mille's" (missing r) from "Miller's", "BESCOM" into "(includinguding BESCOM", etc.

**Detection:** If you see text in a doc that has:
- Missing characters (Mille's instead of Miller's)
- Duplicated characters (TTSed, includeing, ddisputed)
- Characters that should not be there (orphan "et(nldn" mid-word)
- A pattern where the same `find()` offset produces the same wrong deletion on multiple iterations

...you have used text-content positions as document indices.

**Fix — use the structured response:**

```python
# WRONG: pass text-content positions to the API
flat = docs.documents().get(documentId=doc_id).execute()['body']['content']
# ... concat all textRun.content into a string ...
flat_pos = flat.find("in by")  # offset in the flattened string
docs.documents().batchUpdate(documentId=doc_id, body={'requests': [
    {'deleteContentRange': {'range': {'startIndex': flat_pos, 'endIndex': flat_pos+3}}}
]}).execute()  # CORRUPTS the document

# RIGHT: walk the structured content tree
doc = docs.documents().get(documentId=doc_id).execute()  # full structured response
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        for pe in elem['paragraph'].get('elements', []):
            tr = pe.get('textRun', {})
            if 'in by' in tr.get('content', ''):
                # pe['startIndex'] and pe['endIndex'] are DOCUMENT indices
                pos_in_run = tr['content'].find('in by')
                doc_start = pe['startIndex'] + pos_in_run
                doc_end = doc_start + len('in by')  # = 5 chars
                # Now doc_start/doc_end are valid document indices
```

**Alternative for global text substitutions — use `replaceAllText`:** It works on content, not indices. Use it for any change that appears consistently across the document ("in by" → "in", "sq.ft" → "sq. ft.", straight apostrophes → curly). It is completely immune to the text-content-vs-document-index trap.

**The trap also breaks `updateTextStyle` coloring (not just delete/insert):** When you color edited spans (blue/green highlight pattern, see `references/color-coded-doc-updates.md`), a range computed from a flattened or partial text map leaks color into the wrong place. Observed Jul 2026: after `replaceAllText` edits, a script built its text map by walking only top-level `body['content']` paragraphs — table-cell text was missing from the map — so the computed range for a paragraph AFTER a table started ~160 chars too early, painting the tail of the previous paragraph blue. **Fix:** re-fetch the doc and use each paragraph's authoritative `startIndex` from the structured API response (walk recursively INTO tables via `element['table']['tableRows'][...]['tableCells'][...]['content']`), and after styling, reset any leaked neighbor by restyling it back to black (rgb 0,0,0) with the same authoritative ranges. Rule of thumb: only trust `startIndex`/`endIndex` values that come directly from the API response, never offsets you computed by concatenating text.

**Recovery when you've already corrupted the document:** See `references/legal-doc-red-edit-workflow.md` → "Phase 4: Safety net — replaceAllText to fix mangled text" — use `replaceAllText` to fix mangled patterns one at a time.

### 1. InsertText at the wrong index splits paragraphs

When using `insertText`, the index determines WHERE in the paragraph the text lands relative to the paragraph break `\n`:

| Insertion index | Effect |
|---|---|
| `endIndex` of paragraph (e.g. 5251 for `[5240-5251]`) | Right AFTER the `\n` (= between paragraphs) ✅ |
| `endIndex - 1` of paragraph (e.g. 5250 for `[5240-5251]`) | Right BEFORE the `\n` (= inside the paragraph) ❌ splits it |
| `startIndex` of the next paragraph | Same as `endIndex` of previous — also correct ✅ |

**Rule:** To insert content BETWEEN two paragraphs, insert at `endIndex` of the first paragraph (which equals `startIndex` of the next paragraph). Never use `endIndex - 1`.

**Wrong — splits the paragraph:**
```python
# "Next Steps\\n" is at [5240-5251]
# You want to add a new section after "Next Steps"
insertText({"location": {"index": 5250}})  # ⚠️ inserts before \\n, splitting the paragraph!
# Result: "Next Steps" survives at [5240-5250], your text goes at [5250] instead of after the \\n
```

**Correct — between paragraphs:**
```python
# "Next Steps\\n" is at [5240-5251]
insertText({"location": {"index": 5251}})  # ✅ inserts after \\n, between paragraphs
```

**If you already split the paragraph:** The fix is to delete the corrupted range (from the split point to the end of the damage) and re-insert everything cleanly at the correct `endIndex`:

```python
# 1. Delete the corrupted section
deleteContentRange({"range": {"startIndex": 5240, "endIndex": 6190}})
# 2. Insert fresh content at the correct index
insertText({"location": {"index": 5240}, "text": "Next Steps\\n\\nPart 3: New Content\\n\\nRoshni to review..."})
```

Use `startIndex` of the paragraph you want to INSERT BEFORE. If the target section starts at index 6000 and you want to add content just before it, insert at 6000. Content goes between whatever was at 5999 and the target section at 6000.

### 2. The trailing `\n` restriction

Every paragraph element ends with a `\n` character (the paragraph break). **`deleteContentRange` CANNOT include the trailing `\n` of any paragraph segment.** If the range ends at the `endIndex` of a paragraph, which includes `\n`, the API returns `HttpError 400`.

**Fix:** Always subtract 1 from `endIndex` when deleting paragraph text:
```python
# If paragraph at [100-150] contains text ending with \n at [149-150]:
delete_range = {"startIndex": 100, "endIndex": 149}  # excludes \n
```

After deletion, the empty `\n` remains as a structural paragraph marker. Inserting new text at `startIndex` will place it in that paragraph's location.

### 3. Index shift between sequential batchUpdate calls

**Each `batchUpdate` call changes the document.** Indices from the initial document inspection are stale after ANY modification. This is the #1 source of corruption.

**Working backwards strategy (safe within one batchUpdate):**
When deleting multiple paragraphs in the same `batchUpdate` call, order deletions from HIGHEST index to LOWEST index. Earlier (lower-index) content is only affected if you delete content before it.

**Sequential call strategy (safest for complex edits):**
Apply ONE edit per `batchUpdate` call. Re-read the document structure between calls to get fresh indices. This is slower but eliminates index-shift bugs.

```python
# SAFE: one operation at a time
docs.documents().batchUpdate(documentId=doc_id, body={"requests": [delete_op]}).execute()
# Re-read to get fresh indices
doc = docs.documents().get(documentId=doc_id).execute()
# Now calculate next operation's indices from fresh data
```

### 3. replaceAllText shifts indices too

Even `replaceAllText` changes the document length (if replacement text differs in length from original). Always re-inspect the document before doing index-based operations after any `replaceAllText` call.

### 4. Tables have opaque indices

Table cell content is accessible (you can read it from the cell structure) but the `startIndex`/`endIndex` of individual table cells are not directly editable via `deleteContentRange`. To change table content, either:
- Use `replaceAllText` if the cell text is unique enough
- Rebuild the table by deleting and re-inserting (complex)
- Accept that tables require more careful handling

## Pattern: Full section rewrite

For replacing an entire numbered section (heading + body + bullet points):

```python
# 1. Read current indices of the section
# 2. Delete each paragraph's text content sequentially (high-to-low)
for r in reversed_ranges:  # already in descending order
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{"deleteContentRange": {"range": r}}]}
    ).execute()

# 3. Re-read fresh indices
doc = docs.documents().get(documentId=doc_id).execute()
# 4. Find the insertion point (the old section heading position)
# 5. Insert the complete new section text at that position
docs.documents().batchUpdate(
    documentId=doc_id,
    body={"requests": [
        {"insertText": {"location": {"index": INSERT_AT}, "text": NEW_SECTION_TEXT}}
    ]}
).execute()
```

## Modifying Paragraph Background / Shading

You can change the background color of paragraph(s) using `updateParagraphStyle` with the `shading` field. Useful for fixing inherited formatting (e.g. purple/navy backgrounds that don't print well) or styling section headings.

### Set paragraph shading to a specific color

```python
docs = build_service('docs', 'v1')

light_gray = {"rgbColor": {"red": 0.9, "green": 0.9, "blue": 0.9}}

requests = [
    {
        "updateParagraphStyle": {
            "range": {"startIndex": 128, "endIndex": 140},  # from document inspection
            "paragraphStyle": {
                "shading": {
                    "backgroundColor": {"color": light_gray}
                }
            },
            "fields": "shading"
        }
    }
]

docs.documents().batchUpdate(
    documentId=doc_id,
    body={"requests": requests}
).execute()
```

### Remove paragraph shading (make transparent/white)

```python
requests = [
    {
        "updateParagraphStyle": {
            "range": {"startIndex": 1096, "endIndex": 1334},
            "paragraphStyle": {"shading": {}},  # empty object clears it
            "fields": "shading"
        }
    }
]
```

**Note on color values:**
- Each channel is float `0.0`–`1.0` (e.g. `0.5` = 128 in 0-255 scale)
- Light gray for print-friendly headings: `{red: 0.9, green: 0.9, blue: 0.9}`
- Dark navy (common inherited purple/navy from templates): `{red: 0.12, green: 0.22, blue: 0.39}`

### Use case: fixing inherited purple backgrounds

In this session, the original term sheet had dark purple/navy backgrounds on ALL content in sections. The fix:
1. Change heading paragraphs to light gray (`updateParagraphStyle` with `shading.backgroundColor.color.rgbColor = {0.9,0.9,0.9}`)
2. Clear shading on body/content paragraphs (`shading: {}`)
3. Both operations can be bundled in a single `batchUpdate` call since they don't change indices

### Pitfall: batch size limit

Docs API limits `batchUpdate` to 10 requests per call. If you have many paragraphs to re-format, batch them in groups of 10.

```python
for i in range(0, len(requests), 10):
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests[i:i+10]}
    ).execute()
```

## Concrete Index-Shift Bug (and how to avoid it)

### The bug: what happened in this session

After a `replaceAllText` expanded the document (title "TERM SHEET" → "BINDING TERM SHEET" added 7 chars), I tried to replace two neighboring bullets in **separate** `batchUpdate` calls using **original** indices:

```
# Call 1 (worked): Delete [2585-2713], insert new bullet 1 → correct
# Call 2 (corrupted): Delete [2714-2824] → these indices were now WRONG because
#   Call 1 inserted ~600 chars of new text, shifting everything after index 2713
#   The old [2714-2824] now pointed INSIDE the newly-inserted bullet 1 text
```

**Result:** Bullet 1 got the second bullet's text appended as a fragment, and the original bullet 2 survived untouched. Document was corrupted.

### Fix: always re-read indices before each index-based operation

```python
# Step 1: replaceAllText
docs.documents().batchUpdate(...)

# Step 2: Re-read for fresh indices AFTER EACH modification
doc = docs.documents().get(documentId=doc_id).execute()
# ... find new indices ...

# Step 3: Delete paragraph 1 (using fresh indices)
docs.documents().batchUpdate(...)

# Step 4: Re-read again!
doc = docs.documents().get(documentId=doc_id).execute()
# ... find new indices for the next target ...

# Step 5: Delete/insert paragraph 2 with correct indices
```

**Alternative batch approach (for multi-paragraph rewrites):**
If you need to delete N paragraphs and insert new ones in one shot, work from HIGHEST index to LOWEST index within a single `batchUpdate` call. Each earlier (lower-index) target is unaffected by deletions after it:

```python
# All in one batchUpdate call — descending indices
requests = [
    {"deleteContentRange": {"range": {"startIndex": HIGH, "endIndex": HIGH_END}}},
    {"deleteContentRange": {"range": {"startIndex": MID, "endIndex": MID_END}}},
    {"deleteContentRange": {"range": {"startIndex": LOW, "endIndex": LOW_END}}},
    {"insertText": {"location": {"index": LOW}, "text": ALL_NEW_TEXT}},
]
```

**Key rule:** `batchUpdate` processes requests SEQUENTIALLY. Each operation sees the document state after the previous operation, not the original state.

## Complete workflow example

```python
# 1. Copy
drive = build_service('drive', 'v3')
copied = drive.files().copy(fileId=src, body={'name': 'Updated Doc'}).execute()
doc_id = copied['id']
docs = build_service('docs', 'v1')

# 2. replaceAllText for simple stuff
docs.documents().batchUpdate(documentId=doc_id, body={"requests": [
    {"replaceAllText": {"containsText": {"text": "OLD"}, "replaceText": "NEW"}}
]}).execute()

# 3. Re-read for fresh indices (replaceAllText changes document length!)
doc = docs.documents().get(documentId=doc_id).execute()

# 4. For each complex section to rewrite:
#    a. Read current indices
#    b. Delete paragraph text (without trailing \n) — single op per call
#    c. Re-read indices
#    d. Insert new text

# 5. Verify
doc = docs.documents().get(documentId=doc_id).execute()
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        text = ''.join(e.get('textRun', {}).get('content', '')
                       for e in elem['paragraph'].get('elements', []))
        if text.strip():
            print(text.rstrip())

# 6. Hand the link to the user
print(f"Doc link: https://docs.google.com/document/d/{doc_id}/edit")
```
