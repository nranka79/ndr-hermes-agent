# Document Editing Workflow — Financial Calculations

When a user asks you to edit a Google Doc containing calculations (incentive frameworks, budgets, appraisals, etc.):

## Key Rules

**1. Never simplify or restructure first.**
Make only the surgical changes the user explicitly asked for. Preserve ALL original wording, structure, preamble, examples, and formatting. Simplification/restructuring comes only after the user confirms the numbers are right.

**2. Use the original document's totals as-is.**
When applying a split (e.g. 50/50 between two people), take the totals exactly as presented in the original — do not re-derive or recalculate the base values from the line items. Even if the original has malformed or mixed notation (₹ + Cr together), preserve the original numbers and just add the split lines.

**3. Explicit split format.**
Show each scenario like:

```
TOTAL INCENTIVE POOL: ₹X
  → Recipient A (50%): ₹X
  → Recipient B (50%): ₹X
Note: Only Recipient A's share adds to their base pay — the remainder goes to B.
```

**4. Recalculate derived percentages based on the actual share.**
If the original showed "% of fixed pay" on 100%, recalculate it on the recipient's actual share (e.g. 50%). Example: 14.3% of full pool becomes 7.1% on half-share.

**5. Sequence matters.**
- Pass 1: Fix only the numbers (split, percentages)
- Get user confirmation
- Pass 2: Then simplify/restructure if asked

Never combine both in one pass.

## Clarify "Original vs New Doc" First

When a user shares a Google Doc link and says "work on this document" or "fix this document":

- **Assume they mean the original shared doc** — do NOT create a new copy unless they explicitly say "make a copy" or "create a new version"
- Creating a new doc when they expected edits to the original wastes a round-trip and frustrates the user
- If the user specifically says "share back with me", a new doc is appropriate
- When unsure, ask: "Shall I edit the original directly or create a new copy?"

## The "Suggesting Mode" Problem (Docs API Limitation)

**The Google Docs API cannot create suggested edits (tracked changes).** Only direct edits are possible through the API. If the user asks for changes "in suggest mode" or "as suggestions":

1. **Be upfront about the limitation:** Tell them the API doesn't support tracked changes programmatically.
2. **Offer the workaround:** Use Drive API comments to annotate each change instead:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')
comment = drive.comments().create(
    fileId=DOC_ID,
    body={'content': '[Suggestion] Explain what should change and why'},
    fields='id'
).execute()
```

3. **Comments appear as from the user's account** (since their OAuth token is used).

4. **Wording matters** — Keep comments natural and professional. Never use tags like `[RNR Suggestion]` or `[Hermes Note]`. Write as if the user themselves wrote it:
   - ❌ `[RNR Suggestion] Scenario 1 — The total should be split 50/50`
   - ✓ `Suggested revision: The total incentive of ₹3,00,000 should be split 50:50 — ₹1,50,000 to Anbarasan and ₹1,50,000 to the Engineering Team Pool.`

5. **Clean up old/experimental comments** — If you created test comments or unprofessional ones during iteration, delete them before creating the final set:

```python
comments = drive.comments().list(fileId=DOC_ID, fields='comments(id,content)').execute()
for c in comments.get('comments', []):
    if 'test' in c.get('content', '').lower() or '[RNR Suggestion]' in c.get('content', ''):
        drive.comments().delete(fileId=DOC_ID, commentId=c['id']).execute()
```

6. **Alternatively, ask**: "I can make the edits directly (appearing as you) — would you prefer that?"

## Content Replacement in an Existing Document

When replacing text in the middle of an existing document (not at the end), use `deleteContentRange` + `insertText` at the same index:

```python
requests = [
    {
        'deleteContentRange': {
            'range': {
                'startIndex': START,
                'endIndex': END
            }
        }
    },
    {
        'insertText': {
            'location': {
                'index': START  # Same as deletion start
            },
            'text': 'REPLACEMENT TEXT'
        }
    }
]
```

### Find exact indices for replacement

Read the document, build the full text, and use string search to find the target text. Then scan the document's content elements to find the matching `startIndex`/`endIndex`:

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
for i, element in enumerate(doc['body']['content']):
    if 'paragraph' in element:
        for e in element['paragraph'].get('elements', []):
            if 'textRun' in e:
                si = e.get('startIndex')
                ei = e.get('endIndex')
                txt = e['textRun'].get('content', '')
                if 'TARGET_TEXT' in txt:
                    print(f"Element {i}: [{si}-{ei}] '{txt[:80]}'")
```

### Reverse-order processing (critical)

When doing multiple delete+insert operations, **always process from the end of the document to the start** in a single batch. This prevents index shifting:

```python
# Order: scenario 3 → scenario 2 → scenario 1 (document-end first)
requests = [
    # Last section first
    {'deleteContentRange': {'range': {'startIndex': S3_START, 'endIndex': S3_END}}},
    {'insertText': {'location': {'index': S3_START}, 'text': S3_NEW}},
    # Middle section second
    {'deleteContentRange': {'range': {'startIndex': S2_START, 'endIndex': S2_END}}},
    {'insertText': {'location': {'index': S2_START}, 'text': S2_NEW}},
    # First section last
    {'deleteContentRange': {'range': {'startIndex': S1_START, 'endIndex': S1_END}}},
    {'insertText': {'location': {'index': S1_START}, 'text': S1_NEW}},
]
```

If you need to add content BEFORE the edited sections, add those insertions AFTER the scenario fixes in the request array (since they target earlier indices, they won't be affected by later-index operations).

## Formatting Cleanup After Content Edits

After inserting content via the Docs API, auto-applied formatting (especially HEADING_1/2/3) may be inconsistent. Fix it with a diagnostic pass:

### 1. Scan for heading inconsistencies

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
for element in doc['body']['content']:
    if 'paragraph' in element:
        style = element['paragraph'].get('paragraphStyle', {}).get('namedStyleType', '')
        if style != 'NORMAL_TEXT':
            for e in element['paragraph'].get('elements', []):
                if 'textRun' in e:
                    txt = e['textRun'].get('content', '').strip()
                    if txt and len(txt) > 2:
                        print(f"  [{style}] '{txt[:70]}'")
```

### 2. Apply corrective `updateParagraphStyle`

Fix headings that shouldn't be headings (body text that got the wrong style):

```python
requests = [
    {
        'updateParagraphStyle': {
            'range': {'startIndex': BAD_HEADING_START, 'endIndex': BAD_HEADING_END},
            'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT'},
            'fields': 'namedStyleType'
        }
    }
]
```

### 3. Make sub-headings bold (not HEADING_2/3)

When a body section needs emphasis (e.g. "Compensation Structure:", "Collusion Safeguards:"), use bold NORMAL_TEXT instead of a heading level:

```python
{
    'updateTextStyle': {
        'range': {'startIndex': LABEL_START, 'endIndex': LABEL_END},
        'textStyle': {'bold': True},
        'fields': 'bold'
    }
}
```

### 4. Goal

Aim for a clean hierarchy:
- HEADING_1: Major sections (PREAMBLE, numbered top-level sections like 1., 2., etc.)
- HEADING_2: Sub-sections (3.1, 3.2, scenario names, "INCENTIVE POOL SPLIT")
- NORMAL_TEXT: Everything else (body paragraphs, bullet points, calculation lines, process steps)

Avoid orphan heading levels (e.g. a single HEADING_3 in a sea of NORMAL_TEXT) — they look like a mistake.

## Remove a Section and Renumber

When the user asks you to extract a section from a document (e.g., move quality/snag policy out of the incentive framework into a separate doc):

### 1. Find the exact document-structure boundaries

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
for i, element in enumerate(doc['body']['content']):
    if 'paragraph' in element:
        for e in element['paragraph'].get('elements', []):
            if 'textRun' in e:
                txt = e['textRun'].get('content', '')
                si = e.get('startIndex')
                ei = e.get('endIndex')
                if 'SECTION_TO_REMOVE' in txt:
                    print(f"  idx={i} [{si}-{ei}] '{txt.strip()}'")
```

### 2. Delete the range covering the entire section

```python
requests = [{
    'deleteContentRange': {
        'range': {'startIndex': SECTION_START, 'endIndex': SECTION_END}
    }
}]
```

Make sure SECTION_END is the `startIndex` of the *next* section heading you want to keep.

### 3. Renumber remaining sections using `replaceAllText`

After deletion, the remaining sections have stale numbers. Fix them all in one batch:

```python
requests = [
    {'replaceAllText': {
        'containsText': {'text': '3.4 NEW NAME', 'matchCase': True},
        'replaceText': '3.3 NEW NAME'
    }},
    {'replaceAllText': {
        'containsText': {'text': '3.5 ANOTHER NAME', 'matchCase': True},
        'replaceText': '3.4 ANOTHER NAME'
    }},
]
```

### 4. Update cross-references

If other parts of the document reference old section numbers (e.g., "(see Section 3.5)"), fix them too:

```python
{'replaceAllText': {
    'containsText': {'text': '(Section 3.5)', 'matchCase': True},
    'replaceText': '(Section 3.4)'
}}
```

Use `matchCase: True` to avoid accidentally replacing numbers inside calculation values.

### 5. Verify with structured checks

After editing, run targeted assertions rather than dumping the full text:

```python
checks = [
    ("Old section removed", "SECTION_TO_REMOVE" not in text),
    ("New number present", "3.4 CORRECTED_NAME" in text),
    ("Cross-ref updated", "(Section 3.4)" in text),
]
for label, result in checks:
    print(f"  {'✓' if result else '✗'} {label}")
```

## Common Errors to Avoid

- ❌ Re-deriving base numbers from line items instead of using the document's stated totals
- ❌ Restructuring or simplifying alongside calculation fixes
- ❌ Converting the original's notation (e.g. changing Cr to ₹ notation) unless explicitly asked
- ❌ Showing the % of fixed pay based on the full pool instead of the individual's share
- ❌ Creating a separate copy of the document when the user expects edits on the original. When they say "work on the document", assume the original shared doc unless they explicitly say "make a copy first."
- ❌ Making direct edits when the user expects suggesting-mode changes. Always clarify upfront which mode they want.
- ❌ Attempting to create suggested edits via the Docs API — it will silently make direct edits instead
- ❌ Combining simplification/restructuring with calculation fixes in one pass. Fix numbers first, get confirmation, then simplify.
- ❌ Using unprofessional comment tags like "[RNR Suggestion]" — write comments in a natural, professional tone as if the user wrote them.