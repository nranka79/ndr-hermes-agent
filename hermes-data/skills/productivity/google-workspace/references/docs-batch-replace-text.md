# Google Docs — Batch Replace Text (batchUpdate / replaceAllText)

Use `documents().batchUpdate()` with `replaceAllText` requests to replace placeholders in existing Google Docs. This is the programmatic way to fill templates — contracts, affidavits, forms, any document with bracketed placeholders or variable text.

## When to use this

- Filling a template Doc with personalised values (name, date, share count, PAN, amount)
- Updating numbers or percentages across a document (shareholding changes, pricing revisions)
- Removing placeholder markers like `[●]`, `{{NAME}}`, `[...]` from a finished document
- Any bulk find-and-replace in a Google Doc where manual editing would be error-prone

## Prerequisites

- Google Docs API enabled in the Cloud project (it is if Drive/Sheets APIs are — enable it alongside them)
- OAuth scope: `https://www.googleapis.com/auth/documents` (included in `all` service set)
- Must run from `terminal()` with the Hermes venv — NOT from `execute_code` (see `references/gws-bridge-pitfalls.md` §2)

## Pattern

```python
import sys
sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service

# Build the Docs service
service = build_service('docs', 'v1', service_name='google-draas')

doc_id = "1ABC...XYZ"

# Single replacement
requests = [{
    'replaceAllText': {
        'containsText': {
            'text': '{{NAME}}',
            'matchCase': False
        },
        'replaceText': 'Nishant Dinesh Ranka'
    }
}]
service.documents().batchUpdate(
    documentId=doc_id, body={'requests': requests}
).execute()
```

### Multiple replacements in one call

Batch up to ~100 replacements in a single API call for efficiency:

```python
requests = [
    {'replaceAllText': {'containsText': {'text': '{{NAME}}', 'matchCase': False}, 'replaceText': 'Nishant Dinesh Ranka'}},
    {'replaceAllText': {'containsText': {'text': '{{SHARES}}', 'matchCase': False}, 'replaceText': '4,620'}},
    {'replaceAllText': {'containsText': {'text': '{{PERCENT}}', 'matchCase': False}, 'replaceText': '2.23%'}},
    {'replaceAllText': {'containsText': {'text': '{{PAN}}', 'matchCase': False}, 'replaceText': 'AHVPR5168E'}},
    {'replaceAllText': {'containsText': {'text': '{{DOB}}', 'matchCase': False}, 'replaceText': '18 December 1979'}},
]
service.documents().batchUpdate(
    documentId=doc_id, body={'requests': requests}
).execute()
```

### Replacing [●] / black circle placeholders

Indian legal documents use `[●]` (black circle, U+25CF) as placeholders. Replace carefully:

```python
# Replace PAN [●] with actual PAN
# The [●] is three characters: '[' + '●' + ']'
requests = [{
    'replaceAllText': {
        'containsText': {'text': 'Permanent Account Number [●]', 'matchCase': False},
        'replaceText': 'Permanent Account Number AHVPR5168E'
    }
}]
```

**Don't blindly nuke all `[●]` instances** — some may be intentionally in notary/official fields that need manual filling (identification by witness, notary registration number). Be precise with surrounding context in the search string.

## Structural edits: deleteContentRange + insertText (clause rewrites, block removals)

`replaceAllText` only rewrites text *inside* existing paragraphs. To remove an entire clause/paragraph or add a new one, use `deleteContentRange` and `insertText` — they operate on **absolute byte indices** (from `documents().get()` → `body.content[].startIndex/endIndex`).

### Read first, always
Get current indices with a read script that prints every paragraph's `startIndex`, `endIndex`, and text. Indices are the ONLY reliable way to target structural edits.

```python
import sys; sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service
svc = build_service("docs", "v1", service_name="google-draas")
doc = svc.documents().get(documentId=doc_id).execute()
for el in doc.get("body", {}).get("content", []):
    if "paragraph" in el:
        text = "".join(r.get("textRun", {}).get("content", "") for r in el["paragraph"].get("elements", []))
        print(el.get("startIndex"), "\t", el.get("endIndex"), "\t|", text.rstrip("\n")[:110])
```

### Batch ordering rule (CRITICAL)
`batchUpdate` applies requests **sequentially against the mutated doc** — each index-based op shifts subsequent indices. Two safe patterns:

- **Do all index-based structural ops FIRST, ordered from HIGHEST index to LOWEST** (deleting/inserting at high positions never disturbs lower indices), THEN any content-based `replaceAllText` ops (they re-match text on the final state, so order among them doesn't matter).
- If an op would invalidate an index used later (e.g. a delete *before* a planned insert), either reorder or split into a second `batchUpdate` call after re-reading.

Example — remove old clause (c) block, insert replacement at the same spot, insert a new clause after 2.4, delete an old list item:

```python
requests = [
    {"deleteContentRange": {"range": {"startIndex": 8201, "endIndex": 8831}}},   # highest region first
    {"insertText": {"location": {"index": 8201}, "text": "    (c) NEW CLAUSE TEXT...\n"}},
    {"insertText": {"location": {"index": 4578}, "text": "2.5 NEW CLAUSE...\n"}},  # lower, still above 3811
    {"deleteContentRange": {"range": {"startIndex": 3811, "endIndex": 3919}}},     # lowest last
]
```

In this real case the delete at 8201+ didn't affect 4578, and neither touched 3811-3919, so the order worked. When in doubt: highest index → lowest index.

## Known issues

### 1. Unicode handling

The API treats text literally — `₹` (₹ sign, U+20B9) and `\u20b9` are different strings. When reading a doc via `docs_get`, the body text may contain Unicode characters that look identical but have different code points. If a replacement fails silently (no error, no change), try:
- Reading the doc first and inspecting the exact character encoding
- Using broader search terms that avoid the special character
- Testing a shorter surround-context string

### 2. Match order matters

`replaceAllText` operates over the entire document content for each request. If you replace `"29,920"` with `"4,620"` in request 1, and then search for `"4,620"` in request 2 — it will match your own replacement. Chain replacements left-to-right, and use specific surround-context for search strings to avoid cascading matches.

### 3. No partial-match warning

If the old_text doesn't exist in the document, the API returns success with `replaceAllText: {occurrencesChanged: 0}` — no error. Always verify by reading the doc back after updates.

### 4. Leading whitespace kills the match (silent `{}` reply)

Indented list items (clauses like `(a)`, `(f)` in legal docs) store their indentation as **leading spaces inside the text run**. If your match string includes those spaces, it will match; but if you copy the text from a display that trimmed them, the match fails — and the reply is just `{}` (not even `occurrencesChanged: 0`), so it's easy to miss.

**Fix: start the match string at the first distinctive non-whitespace character** and rely on uniqueness of the clause body:

```python
old = "(f) Minimum aggregate sanction: Rs. 90 Crores (Rupees Ninety Crores only), of which ..."  # no leading spaces
```

Also note the batch reply array position: a `{}` for a `replaceAllText` request means ZERO matches — treat it as a failure and re-verify. A successful one returns `{"replaceAllText": {"occurrencesChanged": N}}`.

## Verification pattern (incl. all-black check for legal docs)

```python
from tools.gws_skill_bridge import call
import json

r = call("docs_get", doc_id=doc_id, service_name="google-draas")
data = json.loads(r) if isinstance(r, str) else r
body = data.get("body", "")

# Check key substitutions
checks = ['4,620', 'AHVPR5168E']
for check in checks:
    if check in body:
        print(f"✅ Found '{check}'")
    else:
        print(f"❌ MISSING '{check}'")
```

**For legal docs that must remain all-black** (no redline/blue remnants): iterate `body.content` text runs and assert every `foregroundColor` rgbColor is (0,0,0) or absent (DEFAULT):

```python
non_black = []
for el in doc.get("body", {}).get("content", []):
    if "paragraph" in el:
        for run in el["paragraph"].get("elements", []):
            tr = run.get("textRun", {})
            if not tr: continue
            fg = tr.get("textStyle", {}).get("foregroundColor", {}).get("color", {}).get("rgbColor")
            if fg and (fg.get("red", 0) or fg.get("green", 0) or fg.get("blue", 0)):
                non_black.append(tr.get("content", "")[:60])
assert not non_black, f"NON-BLACK RUNS: {non_black}"
```

For clause-level edits, verify each intended change with an explicit boolean checklist (old text gone + new text present) — catches both silent misses and over-eager replacements (e.g. a phrase you meant to keep that got removed).

## Execution environment

Always run from `terminal()` with the Hermes venv:

```bash
python3 /opt/hermes/.venv/bin/python3 /tmp/your_script.py
```

Or inline:

```bash
cd /opt/hermes && .venv/bin/python3 -c '
import sys; sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service
service = build_service("docs", "v1", service_name="google-draas")
# ... batchUpdate calls ...
'
```
