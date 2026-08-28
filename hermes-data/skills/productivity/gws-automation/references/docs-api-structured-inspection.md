# Google Docs API — Structured Inspection for Formatting Edits

**Status:** Working pattern, confirmed Jul 2026. Complements `docs-api-inspection-and-delivery.md` (which covers structure-level reading) and `docs-api-formatting.md` (which covers writing formatting).

## The docs_get flattening trap

The `gws_skill_bridge.call("docs_get", ...)` wrapper **flattens the document body to a single concatenated text string**. Source (in `tools/gws_skill_bridge.py`):

```python
def docs_get(args):
    service = build_service("docs", "v1")
    doc = service.documents().get(documentId=args.doc_id).execute()
    result = {
        "title": doc.get("title", ""),
        "documentId": doc.get("documentId", ""),
        "body": _extract_doc_text(doc),  # <-- this flattens
    }
```

`_extract_doc_text` walks the structure and joins all `textRun.content` strings into one mega-string. **All element-level structure is lost: `startIndex`/`endIndex`, `textStyle` (color, font, bold, italic), paragraph styles, list membership.**

If you need to do any **structured inspection** (find colored text, find bold runs, find specific font sizes, identify paragraph boundaries for editing), the bridge is the wrong tool. **Bypass the bridge and call `build_service('docs', 'v1')` directly.**

## Working structured inspection recipe

```python
import os, json
os.environ['HERMES_SESSION_USER_ID'] = '[REDACTED-TID]'  # or user's TID
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

docs = build_service('docs', 'v1', service_name='google-draas')
doc = docs.documents().get(documentId=DOC_ID).execute()

# Now `doc` is the full structured response
# doc['body']['content'] is the list of all content elements
# Each has startIndex/endIndex and either 'paragraph', 'table', 'sectionBreak'
```

## Finding colored text runs (purple/brown/red/etc.)

The use case: user has been editing a Google Doc and used colored text to mark changes (e.g., purple for new edits, red for questions). User asks "convert all colored text to black" before sharing the doc with the final recipient.

```python
def find_text_runs_with_color(element, runs=None):
    """Recursively find all textRun elements with non-black foreground color."""
    if runs is None:
        runs = []
    if isinstance(element, dict):
        if 'textRun' in element:
            text = element['textRun'].get('content', '')
            style = element['textRun'].get('textStyle', {})
            color = style.get('foregroundColor', None)
            if color and text:
                runs.append({
                    'startIndex': element.get('startIndex'),
                    'endIndex': element.get('endIndex'),
                    'foregroundColor': color,
                    'text_preview': text[:80],
                })
        for val in element.values():
            find_text_runs_with_color(val, runs)
    elif isinstance(element, list):
        for item in element:
            find_text_runs_with_color(item, runs)
    return runs

colored = find_text_runs_with_color(doc)
print(f"Found {len(colored)} colored text runs")
for r in colored[:20]:
    print(f"  [{r['startIndex']}:{r['endIndex']}] color={r['foregroundColor']} text={r['text_preview']!r}")
```

**Output shape:** A color spec in the Docs API looks like `{'color': {'rgbColor': {'red': 0.44, 'green': 0.19, 'blue': 0.63}}}` for purple. Black is `{'color': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}}`.

## Converting colored text to black — the safe batchUpdate pattern

The 1-line "set everything to black" approach (`updateTextStyle` over the whole document) **erases the user's intent**: if they had intentionally used red for emphasis in a heading, the convert call flattens that too.

To convert only the colored runs, batch-update each one with its specific range. But you must process from **highest index to lowest** to avoid index-shift conflicts:

```python
# Sort colored runs descending by startIndex
colored.sort(key=lambda r: r['startIndex'], reverse=True)

BLACK = {'color': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}}

requests = []
for r in colored:
    requests.append({
        'updateTextStyle': {
            'range': {'startIndex': r['startIndex'], 'endIndex': r['endIndex']},
            'textStyle': {'foregroundColor': BLACK},
            'fields': 'foregroundColor'
        }
    })

# 100 requests per batch (Google API limit)
BATCH = 100
for i in range(0, len(requests), BATCH):
    docs.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': requests[i:i+BATCH]}
    ).execute()
```

**Why reverse order?** Within a single `batchUpdate`, operations apply sequentially and shift later indices. If you process from index 1 upward, every update changes the index of the next one. Processing from highest to lowest means each subsequent operation targets an index that's already been "absorbed" into a lower region — safe.

**Alternative — `replaceAllText` won't work here** because formatting isn't content. You must use `updateTextStyle`.

## Verifying the conversion

```python
# Re-read the doc and re-scan
doc2 = docs.documents().get(documentId=DOC_ID).execute()
remaining_colored = find_text_runs_with_color(doc2)
if not remaining_colored:
    print("✅ All colored text converted to black")
else:
    print(f"⚠️ {len(remaining_colored)} colored runs still remain")
```

## Other inspections the bridge can't do

| Need | Bridge result | Workaround |
|---|---|---|
| Find colored text | flattened → lost | `build_service('docs', 'v1')` + walk structured response |
| Find bold/italic runs | flattened → lost | same |
| Find specific font family/size | flattened → lost | same |
| Count paragraphs vs tables | flattened → lost | same |
| Check named styles (HEADING_1, etc.) | flattened → lost | same |
| Iterate table cells with indices | flattened → lost | same |
| Get raw text | works (via `body` field) | bridge is fine |

## Cross-references

- `docs-api-inspection-and-delivery.md` — structure-level reading and document duplication
- `docs-api-formatting.md` — comprehensive formatting pipeline (font, size, bold, color, indentation, etc.)
- `gws-skill-bridge-drive-operations.md` — same kwarg/arg-name trap on Drive ops
- `color-coded-doc-updates.md` — when to use colored text as a markup signal (and the convert-to-black cleanup step)
