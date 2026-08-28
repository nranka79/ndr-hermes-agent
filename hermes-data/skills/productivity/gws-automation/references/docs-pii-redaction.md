# Google Docs PII Redaction — replaceAllText Workflow

## When to use

- User shares a Google Doc containing personal names, Aadhar numbers, company names, or other PII
- User asks you to redact/rename/anonymize PII directly on the document
- Document has a mix of paragraphs and tables (wills, contracts, agreements, legal docs)

## The core technique

Use `replaceAllText` via Docs API `batchUpdate`. It matches text everywhere — including inside table cells — without needing index calculation. Multiple replacements are batched sequentially in one `batchUpdate` call.

```python
from tools.gws_auth import build_service
docs = build_service('docs', 'v1')

requests = [
    {
        "replaceAllText": {
            "containsText": {"text": "Original Name", "matchCase": True},
            "replaceText": "Role Name"
        }
    }
]
docs.documents().batchUpdate(
    documentId=DOC_ID,
    body={"requests": requests}
).execute()
```

## Step-by-step workflow

### 1. Read the full document structure

Read ALL content — paragraphs AND tables. Tables cannot be ignored because PII lives inside them.

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
body = doc.get('body', {}).get('content', [])
for i, elem in enumerate(body):
    if 'paragraph' in elem:
        text = ''.join(e.get('textRun', {}).get('content', '')
                       for e in elem['paragraph'].get('elements', []))
        print(f'[{i}] {repr(text[:300])}')
    elif 'table' in elem:
        rows = elem['table'].get('tableRows', [])
        for ri, row in enumerate(rows):
            cells = row.get('tableCells', [])
            for ci, cell in enumerate(cells):
                ct = ''
                for ce in cell.get('content', []):
                    if 'paragraph' in ce:
                        for pe in ce['paragraph'].get('elements', []):
                            if 'textRun' in pe:
                                ct += pe['textRun'].get('content', '')
                print(f'  Table row {ri}, cell {ci}: {ct.strip()}')
```

### 2. Map PII to anonymized identifiers

Understand roles before naming:

| Document role | Generic identifier |
|---|---|
| Testator (person making the will) | Settler |
| Executor/trustee | Executor |
| Spouse of testator | Wife / Spouse |
| Children | Eldest Son, Daughter, Second Son, Third Son |
| Spouses of children | Eldest Son's Spouse, etc. |
| Grandchildren | Grandson 1, Grandson 2, etc. |
| Family friend | Family Friend |
| Employee | Employee |
| External entities (companies) | Company 1, Company 2, ... Company N |

### 3. Order replacements strategically within batches

Order matters because `replaceAllText` runs sequentially within a `batchUpdate`:

**PREFIXED NAMES FIRST, THEN BARE NAMES:**
```python
# Order: most specific (with prefix) → bare name
{"replaceAllText": {"containsText": {"text": "Sri. Dinesh Ranka", "matchCase": True}, "replaceText": "Settler"}}
{"replaceAllText": {"containsText": {"text": "Mr. Dinesh Ranka", "matchCase": True}, "replaceText": "Settler"}}
{"replaceAllText": {"containsText": {"text": "Dinesh Ranka", "matchCase": True}, "replaceText": "Settler"}}
```

**TABLE-SPECIFIC VARIANTS BEFORE GENERIC ONES:**
Some tables use different naming (e.g., "Mamta Ranka" in one table, "Mamta Rathod" in another). Handle both:
```python
{"replaceAllText": {"containsText": {"text": "Mamta Rathod (Daughter)", "matchCase": True}, "replaceText": "Daughter"}}
{"replaceAllText": {"containsText": {"text": "Mamta Rathod", "matchCase": True}, "replaceText": "Daughter"}}
{"replaceAllText": {"containsText": {"text": "Mamta Ranka", "matchCase": True}, "replaceText": "Daughter"}}
```

**AADHAR / IDENTIFICATION NUMBERS:**
```python
{"replaceAllText": {"containsText": {"text": "2965 8261 8427", "matchCase": True}, "replaceText": "[Redacted]"}}
```

**COMPOUND LOCATION NAMES BEFORE INDIVIDUAL COMPONENTS:**
When redacting a building name like "2401 Prestige Hermitage", replace the compound first, then fall through to individual words. This prevents partial matches leaving orphan fragments:
```python
# Order: compound phrase → individual components
{"replaceAllText": {"containsText": {"text": "Prestige Hermitage", "matchCase": True}, "replaceText": "[Redacted]"}},
{"replaceAllText": {"containsText": {"text": "2401", "matchCase": True}, "replaceText": "[Redacted]"}},
{"replaceAllText": {"containsText": {"text": "Prestige", "matchCase": True}, "replaceText": "[Redacted]"}},
{"replaceAllText": {"containsText": {"text": "Hermitage", "matchCase": True}, "replaceText": "[Redacted]"}},
```
After the compound match consumes "Prestige Hermitage" at the first step, the individual "Prestige" and "Hermitage" matches are no-ops there but still catch any stray occurrences elsewhere in the document.

**BUILDING NAME VARIANTS:** Catch possessive and non-possessive forms as separate entries:
```python
{"replaceAllText": {"containsText": {"text": "Queens Corner", "matchCase": True}, "replaceText": "[Redacted]"}},
{"replaceAllText": {"containsText": {"text": "Queen's Corner", "matchCase": True}, "replaceText": "[Redacted]"}},
```

**AMOUNT REDACTION:** Redact specific monetary values while preserving the surrounding legal context (e.g., "I wish to gift cash of [Redacted] from my receivables"). Include the currency symbol and any parenthetical word-form for complete coverage:
```python
# Exact amount with words
{"replaceAllText": {"containsText": {"text": "Rs. 9 Crores (Nine Crores Only)", "matchCase": True}, "replaceText": "[Redacted]"}},
{"replaceAllText": {"containsText": {"text": "Rs. 4 Crores (Four Crores Only)", "matchCase": True}, "replaceText": "[Redacted]"}},
# Abbreviated amounts
{"replaceAllText": {"containsText": {"text": "Rs. 10 Cr (Rupees Ten Crore Only)", "matchCase": True}, "replaceText": "[Redacted]"}},
{"replaceAllText": {"containsText": {"text": "Rs. 1Cr", "matchCase": True}, "replaceText": "[Redacted]"}},
```
Do NOT redact amounts the user hasn't asked for (e.g., "Rs. 20Cr" for the wife's share) — verify each amount against the user's instructions.

**CLAUSE REMOVAL (FULL TEXT REPLACEMENT):** When the user asks to remove an entire clause, replace its complete body text with a marker like "[REDACTED - Clause removed]". Read the full paragraph text first, then craft a replaceAllText that matches the ENTIRE paragraph body:
```python
{"replaceAllText": {
    "containsText": {"text": "DISTRIBUTION OF ASSETS DURING MY LIFETIME: It is understood that if, during my lifetime, I gift any of the assets listed herein...",
    "matchCase": True},
    "replaceText": "[REDACTED - Clause removed]"
}}
```
This preserves document structure (paragraph spacing, tables) while scrubbing the content. The marker text tells the reader why content is absent.

**CONTEXT-AWARE REDACTION (DELETE DESCRIPTIVE TEXT, KEEP STRUCTURE):** When the user wants to remove descriptive/identifying details (e.g., "to be spent towards his daughter's wedding") but keep the gift framework, chain two replacements:
```python
# First: redact the amount
{"replaceAllText": {"containsText": {"text": "Rs. 1Cr", "matchCase": True}, "replaceText": "[Redacted]"}},
# Second: delete the descriptive clause after the amount
{"replaceAllText": {"containsText": {"text": "to be spent towards his daughter\u2019s wedding and / or balance to be given to him personally", "matchCase": True}, "replaceText": ""}},
```
The result: "I would like to leave him a sum of [Redacted]." — structurally intact, PII removed.

**WITNESS TABLE BLANKING:** The witnesses section typically has a heading paragraph followed by a 2-column table with placeholder text. Replace both the heading and every cell's content:
```python
# Replace heading
{"replaceAllText": {"containsText": {"text": "WITNESSES:\n", "matchCase": True}, "replaceText": "[REDACTED - Witness section removed]\n"}},
# Replace each cell (index-based per table reading)
{"replaceAllText": {"containsText": {"text": "1.\n\n\n\nName:\nAge:\nAadhar No:\nAddress:", "matchCase": True}, "replaceText": "[Redacted]"}},
{"replaceAllText": {"containsText": {"text": "2.\n\n\n\nName:\nAge:\nAadhar No:\nAddress:", "matchCase": True}, "replaceText": "[Redacted]"}},
```
The table structure with empty cells remains (harmless), but all PII is gone. Note that blank-line spacing inside table cells (\n\n\n\n) must be matched exactly — read the cell content with the line-inspection approach in step 1 to get the precise whitespace.

### 4. Batch size limit: 10 requests per call

Docs API limits `batchUpdate` to 10 requests. Split into groups of 10:

```python
batches = [requests[i:i+10] for i in range(0, len(requests), 10)]
for i, batch in enumerate(batches):
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": batch}
    ).execute()
    time.sleep(0.5)  # rate-limit buffer
```

### 5. Verify after all replacements

Re-read the full document after replacements to catch:
- Unredacted names you missed
- Typos in the original document (e.g., "Mr. Kanta Ranka" instead of "Mrs.")
- Redundant phrasing like "My Wife, Wife" (from "My Wife, Mrs. Kanta Ranka")
- Table cells that didn't match due to whitespace or formatting differences

**FULL-TEXT GREP VERIFICATION:** After re-reading the structured document, also concatenate ALL text (paragraphs + table cells) into a single string and grep for each target term. This catches matches that structural inspection might miss:

```python
# Build full text
all_text = ""
for i, elem in enumerate(body):
    if 'paragraph' in elem:
        text = ''.join(e.get('textRun', {}).get('content', '')
                       for e in elem['paragraph'].get('elements', []))
        all_text += text
    elif 'table' in elem:
        for row in elem['table'].get('tableRows', []):
            for cell in row.get('tableCells', []):
                for ce in cell.get('content', []):
                    if 'paragraph' in ce:
                        for pe in ce['paragraph'].get('elements', []):
                            if 'textRun' in pe:
                                all_text += pe['textRun'].get('content', '')

# Check each term
for term in ['Prestige', '2401', 'Queens Corner', '9 Crores', 'daughter']:
    if term.lower() in all_text.lower():
        idx = all_text.lower().index(term.lower())
        print(f"  LEAK: '{term}' at position {idx}: ...{all_text[max(0,idx-40):idx+80]}...")
```

**VERIFY MARKER TEXT READS NATURALLY:** After redaction, re-read the paragraphs that had context-aware replacements (e.g., amount + descriptive text removal). Check that the resulting sentence flows without orphaned punctuation or awkward gaps. Example: `"[Redacted] ."` (extra space before period) should be cleaned up if possible.

## Pitfalls

### Standalone given names survive surname-only replacements

When you replace full names (e.g., "Ruhaan Ranka" → "Grandson 3"), standalone first names that appear **without the surname** are NOT caught. This happens when the document refers to someone by first name only in a list or compound phrase (e.g., "Ruhaan & Grandson 4" after the surname was already redacted from other occurrences).

**Fix:** After building your replacement list from full names, search the raw text for each person's first/given name in isolation and add separate replaceAllText entries:
```python
# Full name replacement (catches "Ruhaan Ranka" everywhere)
{"replaceAllText": {"containsText": {"text": "Ruhaan Ranka", "matchCase": True}, "replaceText": "Grandson 3"}},
# Standalone first name (catches "Ruhaan" in lists like "Ruhaan & Grandson 4")
{"replaceAllText": {"containsText": {"text": "Ruhaan", "matchCase": True}, "replaceText": "Grandson 3"}},
```

**Catch these in verification:** After applying all replacements, grep the concatenated full text for each person's given name as a standalone word. If it appears, the name replacement was incomplete.

### Iterative round-2: always re-read current state first

When the user comes back with a second batch of redaction requests after an initial pass:

**Always re-read the document's current text before making new changes.** Many items the user lists may already be redacted from the previous round. Proceeding without checking wastes API calls and can cause confusing double-redaction (e.g., "[Redacted] [Redacted]" from two overlapping replacements).

**Workflow for round 2+ :**
```python
# Step 1: Read current state
doc = docs.documents().get(documentId=DOC_ID).execute()
body = doc.get('body', {}).get('content', [])
# ... dump all text to see what's still there

# Step 2: Compare user's list against current text
# Report: "X, Y, Z are already redacted. A, B still need work. C was not found in the document."
# Only apply replacements for items actually still present

# Step 3: Apply and verify
```

**Report back clearly:** In round 2, tell the user which items were already done (so they don't worry about them), which were new and applied, and which weren't found in the document (could indicate a misunderstanding about what's in the doc).

### Semantic edits alongside redaction

Users sometimes want **content rewording** in the same pass as PII redaction — not just replacing text with `[Redacted]` but changing legal phrasing. Example: replacing "perpetual right to use of apartment [Redacted] at [Redacted] that she is currently residing in" with "lifetime right to live in [Redacted]".

These are legitimate replaceAllText operations (string match → new string), not separate edits. Include them in the same batch as redactions — there's no API difference. Just verify the resulting sentence reads naturally.

### User-claimed PII that doesn't exist in the doc

In iterative redaction, users may describe things they *think* are still in the document but were already redacted or never existed. When your search shows the claimed text is absent, **say so directly in your report**. Don't silently skip it — the user needs to know their document is cleaner than they think. This reduces follow-up rounds and builds confidence in the redaction work.

Format:
> Already redacted: [list terms found to already be [Redacted]]
> Not found in document: [list terms user mentioned that aren't present]
> Applied new: [list terms actually changed in this round]

### Interference between name replacements
If you replace "Dinesh Ranka" → "Settler", then later "Nishant Ranka" → "Second Son", these don't interfere because they're separate strings. But watch for:
- Names that are substrings of each other (not common with surnames + given names, but possible)
- Signed/unsigned variants: "(DINESH RANKA)" and "DINESH RANKA" are different strings

### matchCase behavior
- `matchCase: True` (recommended) — exact match, won't accidentally match lowercase variants
- `matchCase: False` — case-insensitive, broader but risky
- Always include prefixes like "Mr.", "Mrs.", "Smt.", "Sri." as separate replacements

### Document ownership and permissions
Check the document owner first via Drive API:
```python
f = drive.files().get(fileId=doc_id, fields='id,name,owners').execute()
```
If the doc isn't owned by the current user, you may get 403 errors or changes won't stick.

### External entities vs. target entities
Don't redact external company names (e.g., "Canara Housing", "Larsen & Tubro") unless the user explicitly asks. These are third-party entities, not PII belonging to the testator or family.

### Unicode apostrophes and smart quotes
Google Docs text frequently uses Unicode smart quotes (\u2018 left single, \u2019 right single, \u201c left double, \u201d right double) rather than ASCII straight quotes. When constructing a replaceAllText string, use Python's repr() to see the exact Unicode characters in the document text:

```python
# Check the raw characters
text = "daughter\u2019s wedding"  # right single quotation mark
# vs
text = "daughter's wedding"       # straight apostrophe
```

If you use the wrong character, the match silently fails. Always read text runs with repr() to verify, or use matchCase=False (risky) for broader matching.

### Multi-pass ordering for comprehensive coverage
When redacting many types of PII (names, locations, amounts, clauses, witness tables), plan the overall pass order:

1. **Read the full document** — paragraph by paragraph AND all table cells
2. **Map all PII** — create a complete list before writing any replacement
3. **Order by specificity** — compound phrases > individual words; exact amounts > partial matches
4. **Batch by type** — group related replacements for legibility (all names, all locations, all amounts)
5. **Verify after ALL batches** — one verification pass at the end, not between each batch

## Comparison with PDF redaction

| Aspect | Google Docs (this workflow) | PDF (pymupdf workflow) |
|---|---|---|
| Method | replaceAllText via Docs API | add_redact_annot + apply_redactions |
| Tables | Handled automatically by replaceAllText | Requires coordinate calculation per cell |
| Document changes | Reversible (edit history) | Irreversible (permanent redaction) |
| Index management | Not needed (string matching) | Must track indices carefully |
| Batch limit | 10 requests per batchUpdate call | No batch limit |

## Concrete session example

This workflow was used to redact a 72-element Last Will and Testament Google Doc containing:
- 18 named individuals (testator, family members, employees, friends)
- 3 Aadhar numbers
- 18 company names appearing across two tables (distribution + Annexure B) and inline text

Total: 67 replaceAllText requests across 7 batches.

**A second pass on the same document added:**
- 4 location/building name redactions (Prestige, Hermitage, Manipal Hospital, Queens Corner variants)
- 4 amount redactions (Rs. 9 Crores, Rs. 4 Crores, Rs. 10 Cr, Rs. 1Cr)
- 1 context-aware deletion (removed wedding detail from employee gift clause)
- 2 full clause removals (replaced with [REDACTED - Clause removed] markers)
- 1 witness section blanking (heading erased + table cells cleared)
- Compound-phrase-first ordering for "Prestige Hermitage" to avoid orphan fragments
