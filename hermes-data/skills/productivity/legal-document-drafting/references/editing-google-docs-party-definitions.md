# Editing Party Definitions in Existing Google Docs via Docs API

When updating party definitions in a live Google Doc (adding "Hereinafter referred to as" labels, renaming parties, adding new numbered parties), use the **Docs API `batchUpdate` with `replaceAllText`** — not HTML re-import, not `docs_append`.

## Why not the other approaches

| Approach | Verdict | Reason |
|----------|---------|--------|
| HTML re-import (Drive upload) | ❌ Overkill | Destroys formatting, lost comments/suggestions, re-creates the doc. |
| `docs_append` | ❌ Wrong tool | Appends to end of doc, can't replace existing text. |
| `batchUpdate` with `replaceAllText` | ✅ Correct | Surgical, preserves all formatting, one API call for multiple changes. |

## Key parameter: `doc_id` not `document_id`

The `gws_skill_bridge.call('docs_get', ...)` function expects the parameter `doc_id`, **not** `document_id`:

```python
# CORRECT
from tools.gws_skill_bridge import call
doc = call('docs_get', service_name='google-draas', doc_id='1abc...')

# WRONG — will raise AttributeError: no attribute 'doc_id'
doc = call('docs_get', service_name='google-draas', document_id='1abc...')
```

When building the service directly via `gws_auth.build_service`, the Docs API v1 takes `documentId` in the `.get()` call itself — only the bridge wrapper uses `doc_id`.

## BatchUpdate Pattern for text replacement

```python
from tools.gws_auth import build_service

docs = build_service('docs', 'v1', service_name='google-draas')
doc_id = '1vXpNnHl7IjboIA6CSwrW4U08Mo-Coj_TfdP0aGkMyJ4'

requests = [
    {
        'replaceAllText': {
            'containsText': {
                'text': 'EXACT STRING TO FIND',
                'matchCase': True   # Legal docs use Title Case consistently
            },
            'replaceText': 'REPLACEMENT TEXT (Hereinafter referred to as "LABEL")'
        }
    },
    # Add more requests for each replacement
]

result = docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': requests}
).execute()

# Check how many matches were found:
for i, reply in enumerate(result.get('replies', [])):
    occ = reply.get('replaceAllText', {}).get('occurrencesChanged', 0)
    print(f'Request {i}: {occ} occurrences changed')
    # 0 means the string wasn't found — check exact text including punctuation
```

## Precise matching: include trailing punctuation

The `replaceAllText` operation matches the **exact string** including punctuation. If the document has a period at the end of a line, include it:

- Document has: `having Aadhaar No. 3722 9379 1618.`
- Search text: `'having Aadhaar No. 3722 9379 1618.'` (with period)
- Replace text: `'having Aadhaar No. 3722 9379 1618 (Hereinafter referred to as "FIRST PARTY NO. 1")'`

If you search without the period, it won't match (or may partially match inside another string).

## Common party-definition edits on Indian legal docs

1. **Add "Hereinafter referred to as" labels** (the use case from this session) — append the phrase after each party's personal details (name, father's name, age, address, Aadhaar). Each party gets its own numbered label.

2. **Renumber parties** — if a new numbered party is inserted, update existing labels to shift numbers.

3. **Update collective description** — e.g., change "three distinct revenue blocks" to "four distinct revenue blocks" (also a `replaceAllText` operation in the same batch).

4. **Add a new party definition block** — requires `insertText` at a specific index (harder; use `replaceAllText` for the preceding/following anchor text + new combined block only if structure is simple).

5. **Remove parties (cascade)** — deleting a party touches far more than its paragraph. Full checklist in `references/land-aggregation-mou-party-restructure.md`. Minimal sequence: delete party paragraph(s) → collapse/reword collective definition (single-party definition if only one remains) → renumber surviving parties → Recital A plural→singular → schedule headers drop party numbers ("FIRST PARTY NO. 1" → "FIRST PARTY") → clause references to party numbers (e.g. 4.2.2) → signature blocks → grep-verify zero leftovers (names + "FIRST PARTY NO.").

## Pitfalls

- **Escape quotes** in Python strings properly when the replacement text contains double-quotes. Best to write the script to a `.py` file and execute it, rather than inline shell `-c` strings — shell escaping for nested quotes is error-prone.
- **Service name resolution**: Always resolve the account via `gws_resolve_account()` before running. Prakash (psingh@draas.com) uses `google-draas`.
- **Never nest** `build_service` inside a `terminal()` subprocess — the vault socket is only available in the sandbox process, not subprocesses. Call `build_service` directly at the top level of your script.
- **Replace order matters** if one search string is a substring of another. Run the more specific replacement first, or use unique anchor text.
- **Verify after update**: Call `docs_get` again and check the output to confirm every party has the expected label.
- **Party-removal lists are LITERAL**: "remove first party 1,3,4" means remove First Party No. 1, No. 3 AND No. 4 — even when the user immediately follows with a role description of First Party No. 1 ("FP1 is the current landowner of Sy 68/1, purchasing 68/2"). The role description describes a NON-PARTY actor (vendor / releasor) whose story goes into a recital — it does NOT mean the party stays. Do not second-guess the removal list based on the description. Apply the list literally, render role descriptions as recitals, and state your interpretation in the summary so a cheap correction round catches any misreading.
