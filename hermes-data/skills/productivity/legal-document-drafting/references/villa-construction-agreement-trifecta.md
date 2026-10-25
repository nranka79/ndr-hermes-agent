# Villa Construction Agreement — Tripartite Party Restructure

For villa/plotted developments where the project land is owned across **multiple entities** (e.g., a Builder/Developer + a Landowner/Confirming Party), the Construction Agreement uses a **three-party structure**:

| Party | Role | Typical Entity |
|-------|------|----------------|
| **FIRST PART** | Promoter / Developer | Company (e.g., DRA Realty Pvt Ltd) |
| **SECOND PART** | Allottee / Purchaser | Individual buyer |
| **THIRD PART** | Confirming Party / Co-Promoter | Land-owning firm/partner |

## Recital Restructure Pattern

When adding a Confirming Party, restructure recitals as follows:

| Recital | Title | Content |
|---------|-------|---------|
| **A** | Project Land — Title & Ownership | Developer's ownership of full project land area with all survey numbers |
| **B** | Title of the Promoter | Developer's specific title documents (sale deeds, GPAs) for their owned surveys |
| **C** | Title of the Confirming Party | Co-Promoter's title documents for their owned surveys |
| **D** | Confirmation & Consent | Co-Promoter confirms **no objection** to Developer acting as sole Promoter — developing, selling, constructing on the joint layout |
| **E–J** | (Existing recitals shifted) | Scheme, Sale Agreement, Engagement, Building Permit, Upfront Payment, Approved Layout Plan |

## Google Docs API — Yellow Highlighting Pattern

Use yellow (`rgbColor 1.0, 1.0, 0.0`) for **pre-registration draft modifications** (party changes, recital restructures, clause edits) in Google Docs.

### Insert+Highlight Workflow

```python
# STEP 1: Insert the new text
insert_requests = [{
    'insertText': {
        'location': {'index': insert_point},
        'text': new_text
    }
}]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': insert_requests}).execute()

# STEP 2: Re-read the document to get new indices
doc = docs.documents().get(documentId=doc_id).execute()
content = doc.get('body', {}).get('content', [])

# Build full_text + segments with absolute indices
full_text = ""
segments = []
for elem in content:
    if 'paragraph' in elem:
        for te in elem['paragraph'].get('elements', []):
            if 'textRun' in te:
                t = te['textRun'].get('content', '')
                st = te.get('startIndex', 0)
                segments.append({'st': st, 'text': t, 'len': len(t)})
                full_text += t

# Helper: relative-to-absolute index mapping
def rel_to_abs(rel_idx):
    acc = 0
    for seg in segments:
        if acc <= rel_idx < acc + seg['len']:
            return seg['st'] + (rel_idx - acc)
        acc += seg['len']
    return None

# STEP 3: Highlight the inserted/changed text
abs_s = rel_to_abs(full_text.find(marker_text))
abs_e = rel_to_abs(full_text.find(end_marker) + len(end_marker))
docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'updateTextStyle': {
            'range': {'startIndex': abs_s, 'endIndex': abs_e},
            'textStyle': {
                'backgroundColor': {
                    'color': {'rgbColor': {'red': 1.0, 'green': 1.0, 'blue': 0.0}}
                }
            },
            'fields': 'backgroundColor'
        }
    }]}
).execute()
```

### Key Pitfalls

- **Indices shift after insertText** — always re-read the document before computing highlight ranges. The insert shifts everything after the insertion point.
- **`replaceAllText` is safer for known-old-to-known-new** — it doesn't require index tracking. Use it for party name changes, recital renumbering, date updates.
- **Page-break / control characters** — `\x0b` chars appear in Docs API output. `replaceAllText` handles them, but `full_text.find()` on concatenated text may need exact character matching.
- **Batch updates with mixed types** — `replaceAllText` and `updateTextStyle` can go in the same batch request array. `insertText` should be separate if subsequent requests depend on the new indices, because indices shift.