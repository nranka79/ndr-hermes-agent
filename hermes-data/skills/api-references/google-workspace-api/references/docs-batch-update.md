# Google Docs batchUpdate — Programmatic Document Editing

The Google Docs API exposes `batchUpdate` for making targeted edits (replace text, insert/delete, style changes) without replacing the entire document. This is the standard way to modify an existing Doc programmatically.

## Auth: Bridge vs Direct

The `gws_skill_bridge` only exposes `docs_get`, `docs_create`, `docs_append`. **There is no `docs_update` / `docs_batch_update` in the bridge** — you must call the API directly.

**Preferred: use `_build_service` from `gws_skill_bridge`** (it loads vault credentials correctly):

```python
from tools.gws_skill_bridge import _build_service
service = _build_service("docs", "v1")
```

**Fallback:** `gws_auth.build_service("docs", "v1")` may fail for non-Nishant users (vault token not found) — see `references/gws-vault-bypass.md`.

## CRITICAL: Field Name — `replaceText` NOT `replaceWithText`

The Google Docs API v1 `replaceAllTextRequest` uses the field **`replaceText`** (not `replaceWithText`). This is a common source of 400 errors.

**✅ Correct:**
```python
{
    "replaceAllText": {
        "containsText": {"text": "search string", "matchCase": True},
        "replaceText": "replacement string"     # ← correct field name
    }
}
```

**❌ Wrong (returns 400):**
```python
{
    "replaceAllText": {
        "containsText": {"text": "search string", "matchCase": True},
        "replaceWithText": "..."     # ← Unknown field → 400 error
    }
}
```

## Method: Raw HTTP (avoids discovery serialization issues)

The Python `google-api-python-client` can mangle field names during serialization. **The most reliable approach** is to send the request body as a raw JSON string via `service._http`:

```python
import json

http = service._http
url = f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate"

body = {
    "requests": [{
        "replaceAllText": {
            "containsText": {"text": "SCHEDULE 'A1'", "matchCase": True},
            "replaceText": "SCHEDULE 'A' (First Party No. 1)"
        }
    }, {
        "replaceAllText": {
            "containsText": {"text": "old text", "matchCase": True},
            "replaceText": "new text"
        }
    }]
}

resp, content = http.request(
    uri=url,
    method="POST",
    body=json.dumps(body),
    headers={"Content-Type": "application/json"}
)

if resp.status == 200:
    result = json.loads(content)
    for reply in result.get("replies", []):
        oc = reply.get("replaceAllText", {}).get("occurrencesChanged", 0)
        print(f"  {oc} occurrence(s) changed")
```

## Multiple Replacements in One Batch

You can send many `replaceAllText` requests in a single `batchUpdate` call. Each request runs sequentially on the document. **Important:** if request N changes text that request N+1 searches for, request N+1 will find 0 occurrences. Order matters — put broad/non-interfering replacements first.

## Common Patterns

### Case-Insensitive Replace

Set `matchCase: False` (or omit the field):

```python
{
    "replaceAllText": {
        "containsText": {"text": "the landowner"},
        "replaceText": "the Landowners"
    }
}
```

### Singular-to-Plural Party References

When restructuring a legal document from one First Party to multiple:

1. Replace the party definition section first (largest unique text block)
2. Replace schedule names (`SCHEDULE 'A1'` → `SCHEDULE 'A'`)
3. Update references throughout: `"the Landowner"` → `"the Landowners"`, `"He shall"` → `"They shall"`
4. Update signature block

### Verifying After Update

**⚠️ Bridge `docs_get` pitfall — table content invisible to text search.**

The `gws_skill_bridge.call("docs_get", ...)` returns a JSON string containing only paragraph text (from `paragraph.elements[].textRun`). **Table cell content is embedded in the JSON structure but NOT in the flat text** — so a simple text search like `if "1,017.39" in result` will return false even when the table cell contains that value.

**✅ Correct: Inspect raw document structure for table data.**

Use `build_service("docs", "v1")` directly and iterate through `body.content`, checking BOTH `paragraph` and `table` elements:

```python
from tools.gws_auth import build_service

service = build_service("docs", "v1", service_name="google-draas")
doc = service.documents().get(documentId=DOC_ID).execute()
content = doc.get("body", {}).get("content", [])

for elem in content:
    if "paragraph" in elem:
        for e in elem["paragraph"].get("elements", []):
            if "textRun" in e:
                body_text += e["textRun"].get("content", "")
    elif "table" in elem:
        for row in elem["table"].get("tableRows", []):
            for cell in row.get("tableCells", []):
                for ce in cell.get("content", []):
                    if "paragraph" in ce:
                        for pe in ce["paragraph"].get("elements", []):
                            if "textRun" in pe:
                                cell_text += pe["textRun"].get("content", "")
```

**Quick spot-check for existing table data:**
```python
# Verify a specific row/column value
for i, elem in enumerate(content):
    if 'table' in elem:
        rows = elem['table']['tableRows']
        for ri, row in enumerate(rows):
            cells = row.get('tableCells', [])
            for ci, cell in enumerate(cells):
                cell_text = ''
                for ce in cell.get('content', []):
                    if 'paragraph' in ce:
                        for pe in ce['paragraph'].get('elements', []):
                            if 'textRun' in pe:
                                cell_text += pe['textRun'].get('content', '')
                if '1,017.39' in cell_text:
                    print(f"Found at table index {i}, row {ri}, cell {ci}")
```

**❌ Wrong — will miss table data:**
```python
result = gws_call("docs_get", service_name="google-draas", doc_id=DOC_ID)
if "1,017.39" in result:   # May be false even when data exists in tables
    print("Found")
```

## Limitations

- `replaceAllText` searches within the document body only — headers/footers/footnotes are separate.
- There is no "replace all across entire doc" that spans all content types.
- Text formatting (bold, italic, font size) is NOT preserved when using `replaceAllText` — the replaced text inherits the formatting of whatever was at that location before replacement. For style-aware editing, use `insertText` + `updateTextStyle` instead.
- Each `batchUpdate` has a maximum request count (practical limit ~50 requests per call).

## Pitfalls

### \x0b (Vertical Tab) Characters in Document Text

Google Docs may insert `\x0b` (vertical tab) characters between text runs — for example between the last text run of one list item and the first text run of the next. When using `replaceAllText`, include `\u000b` in the search string to match these:

```python
{
    "replaceAllText": {
        "containsText": {
            "text": "first item; and\u000b\\nSRI. NEXT PERSON",
            "matchCase": True
        },
        "replaceText": "replacement text"
    }
}
```

Without the `\u000b`, the search will fail to match even though the text appears correct in the rendered document. Use `service._http.request()` (not the discovery client) to send such requests — the client may mangle control characters.

### Inserting New Party Entries via Boundary Replacement

When restructuring legal document parties (e.g. adding a new numbered First Party between existing paragraphs), use a **boundary-anchored replacement**: replace the text that spans the end of one paragraph and the start of the next. This avoids index-drift issues from `insertText`:

```python
{
    "replaceAllText": {
        "containsText": {
            "text": "end of paragraph 3.\\n\\n(All the above First Party No.",
            "matchCase": True
        },
        "replaceText": "end of paragraph 3.\\n\\nFIRST PARTY NO. 4:\\nSRI. SUBRAMANYA, [Details]\\n\\n(All the above First Party No. 1, First Party No. 2, First Party No. 3 and First Party No. 4 shall hereinafter be collectively referred to"
    }
}
```

This single replacement both inserts the new party AND updates the collective definition in one shot — no index calculations needed.

### `_build_service` vs `build_service` for Docs API

When the session user doesn't have a vault token (common for non-Nishant users like Prakash), `tools.gws_auth.build_service("docs", "v1")` fails with `VaultNoTokenError`. Use `from tools.gws_skill_bridge import _build_service` instead — it loads the `google-draas` vault credentials which work for all DRAAS Google Docs:

```python
# ✅ Works for any session user as long as the doc is shared with draas
from tools.gws_skill_bridge import _build_service
service = _build_service("docs", "v1")

# ❌ Fails for users without individual vault tokens
# from tools.gws_auth import build_service
# service = build_service("docs", "v1")
```

Then use `service._http.request()` to send raw JSON batchUpdate payloads (see Method section above).

### Auth Fallback: Skill Module Import + Vault Patching

When `_build_service` fails from a `terminal()` call (e.g. `VaultNoTokenError` or stale session identity), use this alternative: import the skill module directly, patch its `get_credentials` function with the bridge's vault loader, then call its `build_service`:

```python
import sys
sys.path.insert(0, '/opt/hermes')
sys.path.insert(0, '/data/hermes/skills/productivity/google-workspace/scripts')

from tools import gws_skill_bridge
gws_skill_bridge._current_service_name = 'google-draas'  # ← the vault key

import importlib
skill = importlib.import_module('google_api')
skill.get_credentials = gws_skill_bridge._vault_credentials
service = skill.build_service('docs', 'v1')
```

**Why this works:** The skill module's `build_service()` calls `get_credentials()`, which defaults to reading a local token file. Patching it with `gws_skill_bridge._vault_credentials` redirects it to the vault daemon, reading credentials for whatever `_current_service_name` is set to. This bypasses the stale `HERMES_SESSION_USER_ID` / missing `service_name=` parameter issues that can trip up `gws_auth.build_service()` from `terminal()` subprocesses.

**⚠️ Only use this fallback when `_build_service` or `build_service(..., service_name='google-draas')` fails.** The bridge's own `_build_service` is the preferred path — this patching approach is a documented workaround for stubborn session-identity misrouting.

## Pitfall: Paragraph Merging from Wrong deleteContentRange Indices

When using `deleteContentRange` + `insertText` for in-place edits (filling template blanks like `_______________`), **miscalculating the delete range causes adjacent paragraphs to merge into one**.

**Root cause:** Every paragraph element ends with `\n` (the paragraph break). If your `deleteContentRange` includes this `\n`, the API deletes the paragraph boundary — the next paragraph's content flows into the current one, creating a single merged paragraph.

**Example — wrong calculation:**
```python
# Element: "  On the East by: _______________\n"  [startIndex=7728, endIndex=7762]
# Prefix: "  On the East by: " = 18 chars → starts at 7728
# Underscores: "_______________" = 15 chars → starts at 7728+18 = 7746
# Newline: "\n" = 1 char → at index 7746+15 = 7761 (endIndex-1)

# ❌ WRONG — deleted one extra char, eating the \n
deleteContentRange({"range": {"startIndex": 7747, "endIndex": 7762}})
# First underscore char at 7746 survived. \n at 7761 was deleted.
# Result: all boundary lines merge into one paragraph

# ✅ CORRECT — ends at 7761 (exclusive), preserves \n
deleteContentRange({"range": {"startIndex": 7746, "endIndex": 7761}})
```

**Fix pattern for template blanks:**
```python
# 1. Inspect the element to get exact text range
doc = service.documents().get(documentId=doc_id).execute()
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        text = ''.join(e.get('textRun', {}).get('content', '')
                       for e in elem['paragraph']['elements'])
        if '___' in text:
            # Find the exact position of underscores
            prefix_len = text.index('___')  # position of first underscore
            si = elem['startIndex']
            # Delete only the underscores, NOT the \n at endIndex-1
            delete_start = si + prefix_len
            delete_end = si + prefix_len + 15  # 15 underscores
            # ✅ Correct range excludes the \n
```

**Recovery from merged paragraphs:** Delete the entire merged paragraph (all indices) and re-insert the correctly structured text with explicit `\n` characters separating each line. Or use `replaceAllText` on the merged text to split it back apart.
