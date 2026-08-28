# Google Docs API — Creating & Formatting Documents

**See also:** `references/docs-api-tables.md` for table operations.

## Document Formatting Audit & Bulk Standardization Workflow

When a user reports inconsistent formatting (different fonts, sizes, bold mismatches, colored text, uneven spacing), use this multi-pass approach:

### Step 1 — Scan for inconsistencies
```python
doc = docs_service.documents().get(documentId=doc_id).execute()
for elem in doc['body']['content']:
    start = elem.get('startIndex', '?')
    end = elem.get('endIndex', '?')
    if 'paragraph' in elem:
        for e in elem['paragraph'].get('elements', []):
            ts = e.get('textRun', {}).get('textStyle', {})
            text = e.get('textRun', {}).get('content', '').rstrip()
            if text:
                font = ts.get('weightedFontFamily', {}).get('fontFamily', '?')
                size = ts.get('fontSize', {}).get('magnitude', '?')
                bold = ts.get('bold', False)
                color = ts.get('foregroundColor', {}).get('color', {}).get('rgbColor', {})
                # Check for non-black color
                if color and (color.get('red', 0) != 0 or color.get('green', 0) != 0 or color.get('blue', 0) != 0):
                    print(f'NON-BLACK: {text[:40]}')
```

### Step 2 — Fix non-black text first
```python
doc = docs_service.documents().get(documentId=doc_id).execute()
total_end = doc['body']['content'][-1].get('endIndex', 0)
black = {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}

docs_service.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'updateTextStyle': {
            'range': {'startIndex': 1, 'endIndex': total_end},
            'textStyle': {'foregroundColor': {'color': black}},
            'fields': 'foregroundColor'
        }
    }]}
).execute()
```

### Step 3 — Set base font/size on entire document, then override
```python
# Phase A: Set Arial 10pt normal EVERYWHERE (including tables)
requests = [{
    'updateTextStyle': {
        'range': {'startIndex': 1, 'endIndex': total_end},
        'textStyle': {
            'weightedFontFamily': {'fontFamily': 'Arial'},
            'fontSize': {'magnitude': 10, 'unit': 'PT'},
            'bold': False,
            'foregroundColor': {'color': black}
        },
        'fields': 'weightedFontFamily,fontSize,bold,foregroundColor'
    }
}]
# Tables need separate iteration
for tc in table_cells:
    requests.append({
        'updateTextStyle': {
            'range': {'startIndex': tc['start'], 'endIndex': tc['end']},
            'textStyle': {'weightedFontFamily': {'fontFamily': 'Arial'}, 'fontSize': {'magnitude': 10, 'unit': 'PT'}},
            'fields': 'weightedFontFamily,fontSize'
        }
    })
docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

# Phase B: Override specific ranges by category
# Re-read doc for fresh indices
doc = docs_service.documents().get(documentId=doc_id).execute()
# Build a dictionary of text → (start, end) from paragraphs
def find_para(text_fragment):
    for elem in doc['body']['content']:
        if 'paragraph' in elem:
            t = ''.join(e.get('textRun', {}).get('content', '') for e in elem['paragraph'].get('elements', []))
            if text_fragment in t:
                return elem.get('startIndex'), elem.get('endIndex')
    return None, None

requests = []
# Title: 22pt Bold
s, e = find_para('BINDING TERM SHEET')
if s: requests.append({'updateTextStyle': {'range': {'startIndex': s, 'endIndex': e}, 'textStyle': {'fontSize': {'magnitude': 22, 'unit': 'PT'}, 'bold': True}, 'fields': 'fontSize,bold'}})
# Execute Phase B overrides in one batch
if requests:
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

### Common Size/Bold Hierarchy for Business Documents
| Element | Size | Bold | Notes |
|---|---|---|---|
| Document Title | 22pt | Yes | Head of doc |
| Subtitle | 13pt | Yes | E.g. "FOR PURCHASE OF LAND" |
| Section headings | 12pt | Yes | "1. PARTIES", "2. PROPERTY DETAILS" etc. |
| Sub-headings | 11pt | Yes | "Token Advance Payment Details:", "The Buyer shall:" |
| Bullet content | 10pt | No | Body text under bullets |
| Table left col | 10pt | Yes | Field labels |
| Table right col | 10pt | No | Values |
| All other body text | 10pt | No | Location, dates, closing |

**Always: pure black text (`rgbColor: 0,0,0`) — never colored fonts.**

### Indentation Hierarchy for Legal Documents (Deeds, Agreements)

When standardizing indentation in a legal deed or agreement, use a consistent three-level indent scheme:

| Nesting Level | Indent `indentStart` | When to use | Example |
|---|---|---|---|
| 0 — Section headings & signature blocks | 0PT | Clause titles, recital labels, IN WITNESS WHEREOF, signature party blocks, schedule description intro | `"5. REPRESENTATIONS AND WARRANTIES"`, `"WHEREAS:"`, `"IN WITNESS WHEREOF"`, `"CONTRIBUTOR / FIRST PART:"` |
| 1 — Main clauses, recital paragraphs & schedule heading | 18PT | Numbered operative clauses, whereas recitals, schedule title | `"1. The Contributor hereby contributes..."`, `"SCHEDULE A PROPERTY..."` |
| 2 — Sub-clauses & party descriptions | 36PT | Points under a numbered clause, lettered sub-items, party details | `"5.1. The said Property is of clear..."`, `"a) Any breach of..."`, `"Mr. Ashok Kumar, (Aadhar Number:...)"` |

Apply `indentFirstLine` to 0 for all levels (no first-line indent in legal drafting — use paragraph spacing for visual separation instead).

### Common elements in legal deeds and their standard formatting

| Element | Indent | Bold | Size | Alignment | Spacing (above/below) |
|---|---|---|---|---|---|
| Document title | 0PT | Yes | 13pt | CENTER | 6pt / 12pt |
| Section headings (WHEREAS, NOW THEREFORE, 5., 6., etc.) | 0PT | Yes | 11pt | LEFT | 12pt / 6pt |
| "AND" between parties | 0PT | No | 10pt | CENTER | 6pt / 6pt |
| Recital paragraphs (whereas clauses) | 18PT | No | 10pt | LEFT | 0pt / 3pt |
| Operative clauses (1., 2., 3., 4.) | 18PT | No | 10pt | LEFT | 0pt / 3pt |
| Sub-clauses (5.1, 6.1, a), b)) | 36PT | No | 10pt | LEFT | 0pt / 2pt |
| In-clause sub-headings (e.g. "STRICT CAPITAL DEBIT RULE:") | 36PT | Yes | 10pt | LEFT | 0pt / 2pt |
| Schedule title | 18PT | Yes | 11pt | CENTER (or LEFT) | 12pt / 6pt |
| Schedule description body | 0PT | No | 10pt | LEFT | 0pt / 3pt |
| Schedule key-value lines | 36PT | Yes | 10pt | LEFT | 0pt / 2pt |
| "IN WITNESS WHEREOF" | 0PT | Yes | 11pt | LEFT | 14pt / 4pt |
| Signature party labels | 0PT | Yes | 11pt | LEFT | 12pt / 4pt |
| Signature name lines | 0PT | No | 10pt | LEFT | 0pt / 0pt |
| "WITNESSES:" | 0PT | Yes | 11pt | LEFT | 12pt / 4pt |

```python
# Consistent indent application by level
for s, e in heading_ranges:   # Level 0
    requests.append({'updateParagraphStyle': {'range': {'startIndex': s, 'endIndex': e},
        'paragraphStyle': {'indentStart': {'magnitude': 0, 'unit': 'PT'}}, 'fields': 'indentStart'}})
for s, e in main_clause_ranges:  # Level 1
    requests.append({'updateParagraphStyle': {'range': {'startIndex': s, 'endIndex': e},
        'paragraphStyle': {'indentStart': {'magnitude': 18, 'unit': 'PT'}}, 'fields': 'indentStart'}})
for s, e in sub_clause_ranges:   # Level 2
    requests.append({'updateParagraphStyle': {'range': {'startIndex': s, 'endIndex': e},
        'paragraphStyle': {'indentStart': {'magnitude': 36, 'unit': 'PT'}}, 'fields': 'indentStart'}})
```

For signature blocks and signature lines, use 0PT indent — they're visually distinct from the clause body.

### Consistent Paragraph Spacing
```python
# Categorize each paragraph and apply appropriate spacing
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        s, e = elem['startIndex'], elem['endIndex']
        text = ''.join(e.get('textRun', {}).get('content', '') for e in elem['paragraph'].get('elements', []))
        stripped = text.strip()
        
        if not stripped:
            spacing = {'spaceAbove': {'magnitude': 2, 'unit': 'PT'}, 'spaceBelow': {'magnitude': 2, 'unit': 'PT'}}
        elif stripped[0].isdigit() and any(stripped.startswith(f'{i}.') for i in range(1,10)):
            spacing = {'spaceAbove': {'magnitude': 10, 'unit': 'PT'}, 'spaceBelow': {'magnitude': 4, 'unit': 'PT'}}
        elif stripped.startswith('\u2022'):
            spacing = {'spaceAbove': {'magnitude': 3, 'unit': 'PT'}, 'spaceBelow': {'magnitude': 3, 'unit': 'PT'}}
        elif stripped.startswith('   (') or stripped.startswith('    ('):
            spacing = {'spaceAbove': {'magnitude': 1, 'unit': 'PT'}, 'spaceBelow': {'magnitude': 1, 'unit': 'PT'}}
        else:
            spacing = {'spaceAbove': {'magnitude': 2, 'unit': 'PT'}, 'spaceBelow': {'magnitude': 2, 'unit': 'PT'}}
        
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [{
            'updateParagraphStyle': {
                'range': {'startIndex': s, 'endIndex': e},
                'paragraphStyle': spacing,
                'fields': 'spaceAbove,spaceBelow'
            }
        }]}).execute()
```

### Light Gray Section Heading Backgrounds
For print-friendly heading backgrounds:
```python
light_gray = {'rgbColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}}
for heading_text in ['1.  PARTIES', '2.  PROPERTY DETAILS']:
    s, e = find_para(heading_text)
    if s:
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [{
            'updateParagraphStyle': {
                'range': {'startIndex': s, 'endIndex': e},
                'paragraphStyle': {'shading': {'backgroundColor': {'color': light_gray}}},
                'fields': 'shading'
            }
        }]}).execute()
```

## Comprehensive Deed/Contribution Agreement Formatting Pipeline

When starting from a raw Google Doc of a legal deed with multiple formatting inconsistencies, use this complete pipeline:

### Phase 0 — Read & Analyze
```python
doc = docs_service.documents().get(documentId=doc_id).execute()
content = doc.get('body', {}).get('content', [])
for i, elem in enumerate(content):
    if 'paragraph' not in elem:
        continue
    runs = elem['paragraph'].get('elements', [])
    text = ''.join(r.get('textRun', {}).get('content', '') for r in runs if 'textRun' in r).strip()
    has_bullet = 'bullet' in elem['paragraph']
    ps = elem['paragraph'].get('paragraphStyle', {})
    indent = ps.get('indentStart', {}).get('magnitude', 0)
    is_bold = any(r.get('textRun', {}).get('textStyle', {}).get('bold', False) for r in runs if 'textRun' in r)
    print(f'{i:3d} | bullet={has_bullet} | bold={is_bold} | i={indent:>3} | {text[:80]}')
```

### Phase 1 — Content Changes (delete prefixes, insert numbering)
Work from HIGHEST index to LOWEST. Use separate batchUpdate calls, re-reading between phases.

**Step 1a:** Delete unwanted lettered prefixes from WHEREAS clauses (C. → B. → A.)
**Step 1b:** Insert manual numbering on operative clauses (4. → 3. → 2. → 1.)
**Step 1c:** Re-read doc for fresh indices before any formatting.

### Phase 2 — Bullet Cleanup
```python
requests = []
for start, end in party_and_clause_bullet_ranges:
    requests.append({'deleteParagraphBullets': {
        'range': {'startIndex': start, 'endIndex': end}
    }})
docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

### Phase 3 — Apply Text & Paragraph Styles
Work through the document section by section:
1. **Font size first** — set 10pt body text across all content ranges
2. **Section headings** — bold, 11pt, spaced above/below (12pt/6pt)
3. **Indentation** — apply per the hierarchy table above
4. **Special elements** — center "AND", center title, bold schedule key-values
5. **Signature blocks** — no indent, appropriate spacing

### Phase 4 — Verify
Re-read the doc and re-analyze with the same Phase 0 script. Check:
- No remaining bullets where they shouldn't be
- Bold on all section headings, no bold on body text
- Indentation consistent by level
- No colored fonts (all pure black)
- "AND" centered between party descriptions

### Remove unwanted bullets
Use `deleteParagraphBullets` when paragraphs have bullets when they should be plain paragraphs or manually numbered:

```python
requests = []
for start, end in [(130, 556), (2438, 2584), (8159, 8270)]:
    requests.append({
        'deleteParagraphBullets': {
            'range': {'startIndex': start, 'endIndex': end}
        }
    })
docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

### Fix manual numbering in existing documents

Legal documents often use **manually typed** prefixes ("A.", "B.", "C." in WHEREAS clauses) or bullets where numbered clauses are needed ("1.", "2."). The Docs API cannot auto-number paragraphs — you must delete prefixes and insert numbers manually.

**Critical rule — index shift management when combining deletions + insertions:**

Work from HIGHEST index to LOWEST index so earlier operations don't shift later ones.

**Worked example — fixing "A./B./C." → plain text + bullets → "1./2./3./4." in the same doc:**

```python
# ORIGINAL STATE:
# Elem 12: "A. The Contributor holds..."    (starts at 1389)
# Elem 13: "B. The Contributor has agreed..." (starts at 1855)
# Elem 14: "C. The Parties have agreed..."   (starts at 2044)
# Elem 20: bullet "The Contributor hereby..."  (starts at 2447)
# Elem 21: bullet "The Contributor confirms.." (starts at 2590)
# Elem 22: bullet "The Contributor undertakes" (starts at 3033)
# Elem 23: bullet "The Partnership Firm..."    (starts at 3278)

# PHASE 1 — Delete "C. ", "B. ", "A. " (highest index first → no shift conflicts)
docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [
    {'deleteContentRange': {'range': {'startIndex': 2044, 'endIndex': 2047}}},  # "C. "
    {'deleteContentRange': {'range': {'startIndex': 1855, 'endIndex': 1858}}},  # "B. "
    {'deleteContentRange': {'range': {'startIndex': 1389, 'endIndex': 1392}}},  # "A. "
]}).execute()
# After deletions: all content from index 2048 shifts by -9 (3 × 3 chars)

# PHASE 2 — Insert "1. ", "2. ", "3. ", "4. " (highest index first, adjusted for shift)
# After -9 shift: elem 20 at 2438, elem 21 at 2581, elem 22 at 3024, elem 23 at 3269
docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [
    {'insertText': {'text': '4. ', 'location': {'index': 3269}}},  # highest
    {'insertText': {'text': '3. ', 'location': {'index': 3024}}},  # < 3269, unaffected
    {'insertText': {'text': '2. ', 'location': {'index': 2581}}},  # < 3024, unaffected
    {'insertText': {'text': '1. ', 'location': {'index': 2438}}},  # < 2581, unaffected
]}).execute()
# Insertions are at decreasing indices, so no insertion shifts any later insertion's target.

# PHASE 3 — Re-read doc, remove bullets, apply formatting
doc = docs_service.documents().get(documentId=doc_id).execute()
# (use fresh indices for subsequent operations)
```

## Overview

For delivering formatted documents as Google Docs: use Drive API to create the doc (supports parent folder) + Docs API to populate and format.

```python
drive = build_service('drive', 'v3')
doc_file = drive.files().create(body={
    'name': 'TITLE',
    'mimeType': 'application/vnd.google-apps.document',
    'parents': [TARGET_FOLDER_ID]
}, fields='id, name, webViewLink').execute()
doc_id = doc_file['id']
```

## Populating Content

### Insert all text at once
```python
docs = build_service('docs', 'v1')
docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'insertText': {
            'location': {'index': 1},  # Always 1 for fresh doc
            'text': FULL_TEXT
        }
    }]}
).execute()
```

### Find heading / paragraph positions
```python
doc = docs.documents().get(documentId=doc_id).execute()
for elem in doc['body']['content']:
    start, end = elem.get('startIndex'), elem.get('endIndex')
    if 'paragraph' in elem:
        text = ''.join(
            e.get('textRun', {}).get('content', '')
            for e in elem['paragraph'].get('elements', [])
        )
        # text includes trailing \n — use text.rstrip() to check content
```

### Apply formatting
```python
requests = []
requests.append({
    'updateTextStyle': {
        'range': {'startIndex': S, 'endIndex': E},
        'textStyle': {
            'weightedFontFamily': {'fontFamily': 'Arial'},
            'fontSize': {'magnitude': 12, 'unit': 'PT'},
            'bold': True,
            'foregroundColor': {'color': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}}
        },
        'fields': 'weightedFontFamily,fontSize,bold,foregroundColor'
    }
})
requests.append({
    'updateParagraphStyle': {
        'range': {'startIndex': S, 'endIndex': E},
        'paragraphStyle': {
            'spaceAbove': {'magnitude': 10, 'unit': 'PT'},
            'spaceBelow': {'magnitude': 4, 'unit': 'PT'},
            'shading': {'backgroundColor': {'color': {'rgbColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}}}}
        },
        'fields': 'spaceAbove,spaceBelow,shading'
    }
})
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

## CRITICAL — deleteContentRange Constraints

The #1 source of 400 errors. **Cannot include the trailing `\n` of a paragraph** in a delete range.

```
# WRONG — causes "Invalid deletion range" error
{"deleteContentRange": {"range": {"startIndex": 100, "endIndex": 120}}}
# If the content at [119-120] is \n (end of paragraph), this FAILS.

# RIGHT — stop 1 character before the \n
{"deleteContentRange": {"range": {"startIndex": 100, "endIndex": 119}}}
```

**How to identify the safe range:**
- A paragraph element has `startIndex` and `endIndex`. The last character is always `\n`.
- Safe delete range = `{startIndex: start, endIndex: end - 1}` (deletes all content, leaves the `\n`)

**To replace paragraph content:** delete the text (without `\n`), then `insertText` at the same startIndex. The `\n` remains as a structural separator.

## CRITICAL — BatchUpdate Index Shifting

Operations in a **single batchUpdate call are applied SEQUENTIALLY**, not atomically. Each operation changes document indices for subsequent ones in the same batch.

**Safe approach: use one batchUpdate call per logical change, re-reading the doc between calls.**

```python
# Each of these is a SEPARATE batchUpdate call:
docs.documents().batchUpdate(doc_id, body={'requests': [delete_op_1]}).execute()
docs.documents().batchUpdate(doc_id, body={'requests': [delete_op_2]}).execute()
docs.documents().batchUpdate(doc_id, body={'requests': [insert_op_1]}).execute()
```

**If you MUST batch multiple deletes in one call** (to reduce API round-trips): order them from HIGHEST index to LOWEST index, so earlier deletes don't shift indices for later ones.

## replaceAllText — Safer Alternative

For simple text substitutions, use `replaceAllText` — it's content-based and immune to index calculation errors:

```python
{'replaceAllText': {
    'containsText': {'text': 'old text'},
    'replaceText': 'new text'
}}
```

Limitations:
- Replaces ALL occurrences (use unique search strings)
- Case-sensitive by default; pass `'matchCase': False` for case-insensitive
- Cannot change formatting (only text content)
- Works across paragraphs and tables

## Text Inserted via API Lacks Inherited Formatting

Text inserted via `insertText` does NOT automatically inherit the document's default paragraph style (font, size, bold). **Always explicitly set textStyle after insertion:**

```python
# Step 1: Insert text
docs.documents().batchUpdate(doc_id, body={'requests': [{
    'insertText': {'location': {'index': N}, 'text': 'content'}
}]}).execute()

# Step 2: Set formatting on the inserted range
docs.documents().batchUpdate(doc_id, body={'requests': [{
    'updateTextStyle': {
        'range': {'startIndex': N, 'endIndex': N + len('content')},
        'textStyle': {'fontSize': {'magnitude': 10, 'unit': 'PT'}, 'bold': False},
        'fields': 'fontSize,bold'
    }
}]}).execute()
```

**Best practice:** Set the ENTIRE document to your base font/size/bold first, then override specific ranges:
```python
doc = docs.documents().get(documentId=doc_id).execute()
total_end = doc['body']['content'][-1].get('endIndex', 0)

# Set Arial 10pt normal for everything
requests = [{
    'updateTextStyle': {
        'range': {'startIndex': 1, 'endIndex': total_end},
        'textStyle': {
            'weightedFontFamily': {'fontFamily': 'Arial'},
            'fontSize': {'magnitude': 10, 'unit': 'PT'},
            'bold': False
        },
        'fields': 'weightedFontFamily,fontSize,bold'
    }
}]
# Then override specific sections (title, headings, etc.)
```

## updateTextStyle vs updateParagraphStyle

| If you want to change… | Use | fields value |
|---|---|---|
| Font family, size, bold, italic, color | `updateTextStyle` | `'weightedFontFamily,fontSize,bold,foregroundColor'` |
| Paragraph spacing (above/below) | `updateParagraphStyle` | `'spaceAbove,spaceBelow'` |
| Paragraph alignment (left/center/right) | `updateParagraphStyle` | `'alignment'` |
| Background shading (paragraph bg color) | `updateParagraphStyle` | `'shading'` |
| Named style (HEADING_1, NORMAL_TEXT) | `updateParagraphStyle` | `'namedStyleType'` |

### To REMOVE paragraph shading:
```python
{'updateParagraphStyle': {
    'range': {'startIndex': S, 'endIndex': E},
    'paragraphStyle': {'shading': {}},  # empty object clears it
    'fields': 'shading'
}}
```

## Table Cell Formatting

Table cells have their OWN content tree (paragraphs within cells). Iterate them separately:
```python
for elem in doc['body']['content']:
    if 'table' in elem:
        for row in elem['table'].get('tableRows', []):
            for cell in row.get('tableCells', []):
                for p in cell.get('content', []):
                    if 'paragraph' in p:
                        cs, ce = p.get('startIndex'), p.get('endIndex')
                        # Apply formatting to this cell paragraph
```

## Copying a Document

```python
copied = drive.files().copy(
    fileId=SOURCE_ID,
    body={'name': 'New Name'}
).execute()
new_id = copied['id']
```

## Indexing Notes
- Docs API uses 1-indexed positions (index 1 = first character of document body)
- A newline counts as 1 character toward the index
- Inserted text at index 1 pushes everything else forward
- The startIndex of a run is its position IN THE FINAL DOCUMENT

## Helper: find_para() — Locate paragraphs by text content

After every `batchUpdate`, re-read the doc and rebuild a list of paragraphs:

```python
paras = []  # (start, end, text, is_blank)
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        text = ''.join(e.get('textRun', {}).get('content', '')
                       for e in elem['paragraph'].get('elements', []))
        paras.append((elem['startIndex'], elem['endIndex'], text, not text.strip()))

def find_para(fragment):
    for s, e, tx, _ in paras:
        if fragment in tx:
            return s, e
    return None, None
```

Also remember to iterate paragraphs for table cells separately using the table cell content tree.

## Drive — Moving Files/Folders Owned by Other Users

When reorganizing Drive folders, you may encounter the error **"Increasing the number of parents is not allowed"** (HTTP 403). This happens when trying to move a file/folder that is **owned by another Google account**.

### Detection

Always check ownership before attempting to move:
```python
file = drive.files().get(fileId=FILE_ID, fields='id,name,owners').execute()
owners = [o.get('emailAddress') for o in file.get('owners', [])]
if 'ndr@draas.com' not in owners and 'admin2.blr@draas.com' not in owners:
    print(f"Cannot move — owned by {owners}")
```

Folders without a `parents` list (empty `[]`) are typically at My Drive root. If they also show ownership by another account, the `update()` with `addParents` will fail with 403.

### Workaround
The only fix is to ask the owner to move the folder manually, or to share ownership. Document the suggested destination and include it in a summary for the user to forward.

---

## Pitfalls (Quick Reference)
- **deleteContentRange cannot include paragraph-terminating `\n`** — always delete to `endIndex - 1`
- **Batch operations shift indices sequentially** — use separate API calls or re-read between calls
- **Inserted text has no inherited formatting** — always set textStyle explicitly after insertion
- **Text-merging on insertText with `\n`**: When you `insertText` at an index that is the start of an existing paragraph, the text before the first `\n` in your insert goes into a new paragraph and the text AFTER it can merge with the existing paragraph's original content. Insert `\n`+content separately in two insertText calls to avoid merging corruption.
- **Recovering from text merging corruption**: If text got merged (e.g., two paragraphs became one, or content from one paragraph spills into the next), use `deleteContentRange` to remove the corrupted portion, then re-insert correctly. **First** re-read the doc to get fresh indices, **then** delete just the corrupted text (without the trailing `\n` of whichever paragraph you're editing), **then** insert the corrected text. Test with small ranges — large ranges risk index shift errors.
- **`replaceAllText` for fixing corrupted text**: If a paragraph's text got mangled (partial words merged, missing content), use `replaceAllText` with unique strings to surgically fix it without index math. Works across all paragraphs and tables. Example: fixing "Mode of: RTGS" → "Mode of Payment: RTGS".
- **Don't use Docs API to create docs with parent folders** — use Drive API for creation, then Docs API for content
- **Formatted docs can't be created with initial content** — always create empty doc, then insert text
- **Tables need cell-by-cell iteration** — they don't appear in the flat paragraph list
- **`replaceAllText` works on ALL occurrences** — use unique enough strings to avoid unwanted matches
- **Line spacing + font changes can cause text superimposition**: When creating a fresh doc, inserting text, then applying `updateTextStyle` (fontSize) and `updateParagraphStyle` (lineSpacing) in subsequent batch updates, the text can render overlapping/superimposed. **Avoid setting `lineSpacing` via API on newly created docs** — let Google Docs use its native default. If you must adjust spacing, set per-paragraph `spaceAbove`/`spaceBelow` instead of touching `lineSpacing`.
