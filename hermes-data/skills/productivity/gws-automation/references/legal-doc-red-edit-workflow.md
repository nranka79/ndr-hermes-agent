# Legal Document Red-Edit Workflow — Docs API

**When:** A user asks you to edit an existing legal document (MOU, agreement, term sheet) and wants all changes visible in RED ink (redlining/change tracking). Used for MOU drafting, contract amendments, and legal document review cycles.

**See also:** `references/color-coded-doc-updates.md` (green/blue reviewer highlights for template-based docs), `references/docs-api-editing-existing.md` (general batchUpdate reference)

## The RED-Edit Pattern

Unlike green/blue highlights (used for reviewer visibility on template copies), RED text is the **legal redlining convention** — it shows what was changed so both parties can review. Every substantive modification must be in RED.

| Aspect | Value |
|--------|-------|
| RED color RGB | `(0.8, 0.0, 0.0)` — bold red, not pink |
| What to mark RED | Party name changes, replaced clauses, new sections, alignment/format corrections |
| What NOT to mark | Existing text left unchanged, tables with no modifications, signature blocks |

## Full Workflow (MOU/Agreement Editing)

```
Phase 1: replaceAllText for global substitutions
↓
Phase 2: Re-read doc for fresh indices (CRITICAL — DO NOT SKIP)
↓
Phase 3: batchUpdate with index-based edits (deleteContentRange + insertText)
↓
Phase 4: Re-read → identify any corrupted/mangled text
↓
Phase 5: Safety net — replaceAllText to fix mangled text
↓
Phase 6: Color all changed text RED
↓
Phase 7: Final verification / share link
```

### Phase 1 — Global Text Replacements

Start with `replaceAllText` for all simple substitutions. Bundle all in one call:

```python
requests = [
    {
        "replaceAllText": {
            "containsText": {"text": "SATVIK DEVELOPERS", "matchCase": True},
            "replaceText": "DRA KAAJ DEVELOPMENT PARTNERS"
        }
    },
    {
        "replaceAllText": {
            "containsText": {"text": "Satvik Developers", "matchCase": True},
            "replaceText": "DRA KAAJ Development Partners"
        }
    },
    {
        "replaceAllText": {
            "containsText": {"text": "Represented by its authorized representative Mr. Nishant Ranka,"},
            "replaceText": "Represented by its Partners,"
        }
    },
]
docs.documents().batchUpdate(documentId=DOC_ID, body={"requests": requests}).execute()
```

### Phase 2 — Re-read for Fresh Indices

**CRITICAL — DO NOT SKIP.** `replaceAllText` changes document length. Any index from the original read is now stale.

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
content = doc["body"]["content"]
for i, elem in enumerate(content):
    for pe in elem.get("paragraph", {}).get("elements", []):
        tr = pe.get("textRun", {})
        if tr.get("content"):
            print(f"E{i}: [{pe['startIndex']}-{pe['endIndex']}] {repr(tr['content'][:80])}")
```

Save this output to a file or use `search_files` with the changed terms to verify replacements landed correctly before proceeding.

### Phase 3 — Index-Based Edits (deleteContentRange + insertText)

For replacing specific clauses, fixing WHEREAS text, changing alignment:

```python
requests = [
    # Delete old text (exclude trailing \n — see pitfall below)
    {"deleteContentRange": {"range": {"startIndex": 6091, "endIndex": 6504}}},  # -1 for \n
    # Insert new text at same position
    {"insertText": {"location": {"index": 6091}, "text": NEW_CLAUSE_16}},
]

# Apply ONE batch, then re-read before next batch
docs.documents().batchUpdate(documentId=DOC_ID, body={"requests": requests}).execute()
```

**Key rule: ONE batch per logical operation, re-read between batches.** Complex multi-edit sequences MUST be broken into individual batches with re-reads in between, because each batch shifts all subsequent indices.

### Phase 4 — Safety Net with replaceAllText

Index operations WILL go wrong sometimes (offset miscalculation, stale index from missed re-read). When they do, the text will be mangled — fragments of old and new text concatenated, missing spaces, duplicated prefixes.

**Don't try to fix with more index operations — use replaceAllText:**

```python
# After a botched delete+insert, text looks like:
# "Partnershipthe is  absolute" instead of "Partners is the absolute"
# Don't calculate delete ranges for individual chars — just:

result = docs.documents().batchUpdate(documentId=DOC_ID, body={"requests": [
    {"replaceAllText": {
        "containsText": {"text": "Partnersthe is"},
        "replaceText": "Partners is the"
    }}
]}).execute()
```

`replaceAllText` is immune to index shift — it finds text by content, not position. Use it liberally as a cleanup tool.

### Phase 5 — RED Color Application

Color all changed text elements RED. Re-read to find them:

```python
RED = {"foregroundColor": {"color": {"rgbColor": {"red": 0.8, "green": 0.0, "blue": 0.0}}}}
doc = docs.documents().get(documentId=DOC_ID).execute()

red_ops = []
for elem in doc["body"]["content"]:
    for pe in elem.get("paragraph", {}).get("elements", []):
        tr = pe.get("textRun", {})
        if tr.get("content"):
            text = tr["content"]
            # Match by content pattern: new clauses, replaced names, new sections
            if any(pattern in text for pattern in [
                "DRA KAAJ",          # All name replacements
                "17. ", "18. ", "19. ", "20. ", "21. ", "22. ", "23. ", "24. ",  # New clause numbers
                "DISPUTE RESOLUTION", # Replaced clause 16
                "Represented by its Partners",  # Updated representative clause
                "JOINT MONETIZATION", "LAND AGGREGATION", "CONSIDERATION",
                "REGISTRATION AND PAYMENT", "ROLE OF THE FIRST",
                "OPTIONS FOR DEVELOPMENT", "SHARING OF PROCEEDS",
                "CONTINUING OBLIGATIONS"
            ]):
                red_ops.append({
                    "updateTextStyle": {
                        "range": {"startIndex": pe["startIndex"], "endIndex": pe["endIndex"]},
                        "textStyle": RED,
                        "fields": "foregroundColor"
                    }
                })

# Batch in groups of 10 (Docs API limit)
for i in range(0, len(red_ops), 10):
    docs.documents().batchUpdate(
        documentId=DOC_ID,
        body={"requests": red_ops[i:i+10]}
    ).execute()
```

### Phase 6 — Fixing WHEREAS Clause Alignment

Legal documents often have WHEREAS clauses formatted as CENTER when they should be JUSTIFIED. Fix via `updateParagraphStyle`:

```python
requests = [{
    "updateParagraphStyle": {
        "range": {"startIndex": elem_start, "endIndex": elem_end},
        "paragraphStyle": {
            "alignment": "JUSTIFIED",  # or LEFT
            "lineSpacing": 115,
            "spaceAbove": {"magnitude": 6, "unit": "PT"},
            "spaceBelow": {"magnitude": 6, "unit": "PT"},
            "indentFirstLine": {"magnitude": 18, "unit": "PT"}
        },
        "fields": "alignment,lineSpacing,spaceAbove,spaceBelow,indentFirstLine"
    }
}]
```

## Cross-Sourcing Party Details from Prior Sessions

**When:** A user says "you have all details of [entity] from [prior document] which was recently done — enter those details in this deed." The details (partner names, addresses, PAN, Aadhaar, CIN, registered office) exist in a document created or discussed in a past Hermes session, and need to be woven into the current document's party description.

### Step 1 — Find the Prior Session

Use `session_search` with multiple query attempts — entity name variants, document type, user's phrasing:

```python
session_search(query="reconstitution deed dra muthanalur", limit=5)
# If empty, try variants:
session_search(query="Muthanalur dra kaaj partners", limit=5)
```

The prior session transcript contains the full document content (either as tool output from a document creation, or as OCR text from a PDF). Read the session to extract the needed details.

### Step 2 — Identify What Needs Updating

The document currently has a brief party description (typically 3 lines):

```
DRA KAAJ DEVELOPMENT PARTNERS,
Represented by its Partners,
Registered Office at Bangalore.
```

This must be expanded to include:
- Full firm name with M/s. prefix
- Constitution (Partnership Firm registered under the Indian Partnership Act, 1932)
- Full registered office address (not just "Bangalore")
- Sub-listing of each partner with their individual details (CIN/PAN/Aadhaar/address)

### Step 3 — Replace the Brief Party Description

Use `deleteContentRange` + `insertText` in a single batch to replace the old lines:

```python
# Step 3a: Read current indices from the doc
doc = docs.documents().get(documentId=DOC_ID).execute()
# Find the SECOND PARTY section — typically elements like:
# E[N]: "DRA KAAJ DEVELOPMENT PARTNERS,\n"    [615-646]
# E[N+1]: "Represented by its Partners,\n"     [646-675]
# E[N+2]: "Registered Office at Bangalore.\n"  [675-707]
# E[N+3]: "\n"                                  [707-708]

# Step 3b: Delete the old 3 lines (exclude trailing \n from last paragraph)
# Range is 615-707 (endIndex of last line minus 1 for its trailing \n)
old_start = 615
old_end = 707  # subtract 1 for \n

# Step 3c: Insert the expanded description at the same position
expanded_text = """M/s. DRA KAAJ DEVELOPMENT PARTNERS,
A Partnership Firm registered under the Indian Partnership Act, 1932,
Having its Registered Office at 201A/202BA, Queens Corner, No. 3, Queens Road, Bangalore – 560 001,
Represented by its Partners.

The Partners of DRA KAAJ Development Partners are:

(i) DRA REALTY PRIVATE LIMITED, a company incorporated under the Companies Act, 2013, bearing CIN U70100KA2011PTC058105, having its registered office at 201A/202BA, Queens Corner, No. 3, Queens Road, Bangalore – 560 001, represented by its Director, Mr. NISHANT DINESH RANKA (Aadhaar No. 4159 0535 2796); and

(ii) Mr. ASHOK KUMAR, Son of Mr. Ram Kumar, aged about 55 years, residing at B-27, Zonasha Paradise, Near Alpine Eco Apartment, Doddanekundi, Bengaluru – 560 037, bearing Aadhaar No. 8751 3355 3386 and PAN ANBPK6960D.
"""

requests = [
    {"deleteContentRange": {"range": {"startIndex": old_start, "endIndex": old_end}}},
    {"insertText": {"location": {"index": old_start}, "text": expanded_text}},
    {"updateTextStyle": {
        "range": {"startIndex": old_start, "endIndex": old_start + len(expanded_text)},
        "textStyle": {"foregroundColor": {"color": {"rgbColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}}},
        "fields": "foregroundColor"
    }}
]
docs.documents().batchUpdate(documentId=DOC_ID, body={"requests": requests}).execute()
```

**Important:** Unlike Phase 1's `replaceAllText` (which uses case-sensitive content matching), the party header section is at a fixed index position. The `deleteContentRange` precisely removes the old 3 lines, and `insertText` puts the expanded description in their place. Since the deletion + insertion happen in the same batch, the insert correctly targets index `old_start` (which is after the preceding text, not after the deleted text).

### Step 4 — Keep RED for all Expanded Content

The `updateTextStyle` in the same batch call applies RED to the entire newly inserted text. This ensures the expanded party description is visibly marked as a change — critical for legal redlining conventions.

### Data Extraction Pattern (from Session Transcripts)

Prior session transcripts store full document content in tool output. Key fields to extract:

| Field | Where to find in session | Example |
|-------|--------------------------|---------|
| Firm constitution | From "A Partnership Firm registered under the Indian Partnership Act, 1932" | Partnership firm |
| Registered office | "registered office at" clause in the deed | 201A/202BA, Queens Corner... |
| Partner company CIN | Company details section | U70100KA2011PTC058105 |
| Partner Aadhaar | Partner personal details | 4159 0535 2796 |
| Partner PAN | Partner personal details | ANBPK6960D |
| Representative name | "represented by its" clause | Mr. NISHANT DINESH RANKA |

**Pitfall:** Session data may contain multiple document drafts with different detail levels. Use the LATEST finalized version (typically the one the user confirmed). Cross-check party names against the current document — if the reconstitution deed shows partner A and partner B, but the MOU only needs the firm-level description, present the firm with its constituent partners listed under it.

### Consistency with FIRST PARTY Description

Match the expanded SECOND PARTY description to the FIRST PARTY's level of detail. If the FIRST PARTY lists:
- Full name
- Representative with full name and father's name
- Registered office address
- PAN number

Then the SECOND PARTY should list the same level of detail for both the firm and each constituent partner.

## Common Pitfalls

### 1. The Index Drift Trap

**Scenario:** You run `replaceAllText` (Phase 1) which changes 4 occurrences of "SATVIK DEVELOPERS" (16 chars) → "DRA KAAJ DEVELOPMENT PARTNERS" (31 chars) = +60 chars total. Then in Phase 3 you try to `deleteContentRange` using indices read from the ORIGINAL doc before Phase 1. **Every index is now wrong by +60 (or more).**

**Fix:** Always re-read the full document between Phase 1 and Phase 3. Keep a script file you can re-run to dump current indices.

### 2. The Sequential Batch Index Trap

Within a single `batchUpdate` call, operations are processed sequentially — each one sees the state AFTER the previous one. This means:

```python
# BAD: These use the SAME delete range twice, but the second one
# targets a range that shifted after the first delete
requests = [
    {"deleteContentRange": {"range": {"startIndex": A, "endIndex": B}}},
    {"deleteContentRange": {"range": {"startIndex": A+delta, "endIndex": B+delta}}},
    # This is WRONG — after the first delete, A+delta has shifted
]
```

**Always re-read between batches. Do not trust calculated offsets.**

### 3. Trailing \n in deleteContentRange

Every paragraph ends with a `\n` character. The range `[startIndex, endIndex)` in `deleteContentRange` CANNOT include this `\n`. Always subtract 1 from `endIndex`:

```python
# Paragraph at [6091-6505], where 6505 is the \n:
delete_range = {"startIndex": 6091, "endIndex": 6504}  # exclude \n
```

### 4. replaceAllText as Index-Safe Cleanup

When index operations produce mangled text (missing spaces, concatenated words, leftover characters), reach for `replaceAllText` — it's index-safe and can fix across the entire document in one call.

Mangled patterns that `replaceAllText` can fix:
- `"Partnersthe is"` → `"Partners is the"` (missing space, wrong word order)
- `"re represented by its"` (leftover prefix from partial deletion)
- `"e16. DISPUTE"` (leftover character from old text)
- `"16. If any dispute16. DISPUTE"` (duplicate prefix from incomplete deletion)

### 5. Finding "SCHEDULE A PROPERTY" — Watch for False Positives

When searching for section headers like "SCHEDULE A PROPERTY", note that this text appears TWICE in most legal docs:
1. As a bold reference term in WHEREAS clause A: `..."SCHEDULE A PROPERTY" herein.\n"`
2. As the actual section header: `"SCHEDULE A PROPERTY\n"` (no trailing quote or "herein")

Always check the surrounding text to distinguish:
```python
# Look for the standalone header (not the WHEREAS reference)
if tr["content"].strip() == "SCHEDULE A PROPERTY" and "herein" not in tr["content"]:
    # This is the actual section header
```

## Complete Session Flow (MOU Rewrite Example)

From real sessions (Jun 2026), the end-to-end flow for editing a DRA KAAJ Development Partners MOU:

### Flow A — Standard MOU Rewrite (Phase-based)

1. **Phase 1** — `replaceAllText`: SATVIK DEVELOPERS → DRA KAAJ DEVELOPMENT PARTNERS (×4), Satvik Developers → DRA KAAJ Development Partners (×2), representative name → Partners
2. **Apply RED** to all "DRA KAAJ" instances found by re-reading
3. **Fix alignment** — WHEREAS clauses CENTER → JUSTIFIED
4. **Replace Clause 16** — Arbitration → Binding Mediation
5. **Remove mangled text** — `replaceAllText` to clean up "Partnersthe is" → "Partners is the"
6. **Insert new clauses 17-24** — Joint Monetization, Land Aggregation, Consideration, Registration, First Party Role, Development Options, Sharing, Continuing Obligations
7. **Color all new clauses RED**
8. **Verify** — dump full document structure, check each section

Total: ~6 batches, 2-3 fix rounds for index drift.

### Flow B — With Cross-Sourced Party Details (adds upstream step)

0. **Cross-source entity details** — User says "you have all details from the reconstitution deed of [Entity A] which was recently done."
   - Use `session_search` with entity name + "reconstitution deed" to find the prior session
   - Extract partner details (names, CIN, PAN, Aadhaar, addresses, registered office) from the session transcript
   - Keep a reference mapping of what goes where
1. **Phase 1** — `replaceAllText` for global substitutions
2. **Re-read doc** for fresh indices
3. **Expand party description** — Replace the brief 3-line SECOND PARTY description with the full multi-paragraph version listing all partners and their details (see Cross-Sourcing section above). Color RED in the same batch.
4. **Continue with Phase 3-8** — Clauses, mediation, alignment, etc.
5. **Final verification** — Check both the substituted names AND the expanded party section render correctly.

Total: ~7 batches, same 2-3 fix rounds plus one extra read round for the expanded section.
