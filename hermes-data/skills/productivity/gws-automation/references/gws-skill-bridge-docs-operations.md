# gws_skill_bridge Docs Operations — kwarg/arg-name mismatch trap

**Status:** Working pattern, confirmed Jul 2026.

## What the bridge does

`tools.gws_skill_bridge.call(operation, **kwargs)` creates a `SimpleNamespace` from kwargs, then passes it to the skill function which reads attributes like `args.doc_id`, `args.title`, `args.text`. The parameter names differ from what you'd guess from the Google Docs v1 API.

## Operations & the kwarg names that ACTUALLY work

| Operation | Working kwargs | Notes |
|---|---|---|
| `docs_get` | `doc_id=...` | NOT `document_id`, NOT `id`. Returns a JSON object with `title`, `documentId`, and `body`. ⚠️ **The body is a single flattened text string** — all structural info (paragraph boundaries, textStyle runs, heading levels) is lost. For element-level inspection, use `build_service('docs', 'v1').documents().get().execute()` directly. |
| `docs_create` | `title=...`, `body=...` | `title` = document title. `body` = initial content text (plain string, not HTML or markdown). Returns JSON with `documentId` and `url`. |
| `docs_append` | `doc_id=...`, `text=...` | NOT `document_id` or `content`. `text` = plain string to append at the end of the document. Returns JSON with `documentId` and `inserted_at` index. |

## What bit me (AttributeError)

- **First call used `document_id`** → raised `AttributeError: 'types.SimpleNamespace' object has no attribute 'doc_id'`. The skill reads `args.doc_id` for both `docs_get` and `docs_append`.
- **First call for `docs_append` used `content=...`** instead of `text=...` — same AttributeError. The skill reads `args.text`.

## Working recipes

### Read a Google Doc (flattened text)

```python
from tools.gws_skill_bridge import call

result = call("docs_get", service_name="google-draas",
              doc_id="1QvSBJIOtvCNfehltsY6D5XMiUscmxYzUxJc6eQQGthA")
# Returns: {"title": "Document Title", "documentId": "...", "body": "Full text content..."}
```

### Create a new Google Doc

```python
result = call("docs_create", service_name="google-draas",
              title="My Doc",
              body="Initial content here.")
```

### Append text to an existing Doc

```python
result = call("docs_append", service_name="google-draas",
              doc_id="1QvSBJIOtvCNfehltsY6D5XMiUscmxYzUxJc6eQQGthA",
              text="Additional text to add at the end.")
```

## When to bypass the bridge

The bridge's `docs_get` flattens the document body to a single text string — all `startIndex`/`endIndex`/`textStyle` (color, font, bold, italic) and structural element information is lost. You CANNOT:

- Find colored text runs (e.g., RED in legal red-edit tracking)
- Detect heading levels (H1/H2/H3 vs body)
- Identify paragraph boundaries
- Locate tables, lists, or inline objects
- Read specific named styles

For any of these, bypass the bridge and use `tools.gws_auth.build_service()` directly:

```python
from tools.gws_auth import build_service

docs = build_service("docs", "v1", service_name="google-draas")
doc = docs.documents().get(documentId="1QvSBJIOtvCNfehltsY6D5XMiUscmxYzUxJc6eQQGthA").execute()

# Full element tree — each element has startIndex, endIndex, paragraph, textRun, textStyle, etc.
for elem in doc.get("body", {}).get("content", []):
    if "paragraph" in elem:
        for para_elem in elem["paragraph"]["elements"]:
            if "textRun" in para_elem:
                text = para_elem["textRun"].get("content", "")
                style = para_elem["textRun"].get("textStyle", {})
                color = style.get("foregroundColor", {}).get("color", {}).get("rgbColor")
                if color:
                    print(f"  Color: {color}")
```

See `references/docs-api-structured-inspection.md` in this skill for the full element-level inspection pattern.

## Pitfalls

- **`doc_id` not `document_id`** — always use `doc_id` for `docs_get` and `docs_append`.
- **Flattened body is a read-only limitation** — the bridge gives you the text content as one long string. You cannot pinpoint where one paragraph ends and another begins. Only use the bridge when you need the full text and structure doesn't matter (e.g., searching for keywords, extracting all text).
- **For structured edits (append at a specific position, insert tables, modify styles):** Use the raw Docs API directly via `build_service()`. The bridge only supports `docs_append` which adds text at the very end.
- **Body is in the `body` key, not `content`** — the bridge returns `{"body": "text..."}`, not the raw API response shape.
- **Flattened body includes page/section breaks as whitespace** — don't rely on line count for structure.
- **`service_name` defaults to `"google-draas"`** — pass explicitly for multi-account setups.
- **Output is always JSON on stdout** — `call()` returns a string. Parse with `json.loads()`.
- **Calendar operations have their own parameter quirks** — see `references/gws-skill-bridge-calendar-operations.md`. Same SimpleNamespace pattern: `calendar_create` needs `location=''`, `attendees=''`, `calendar='primary'` explicitly passed.
