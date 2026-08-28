# Color-Coded Document Updates for Reviewer Visibility

**When:** You've made multiple incremental updates to a Google Doc that a reviewer (Prakash, Nishant, etc.) needs to verify. Use colored text to visually flag what changed.

## Pattern

| Color | Meaning | RGB | Use Case |
|-------|---------|-----|----------|
| 🟢 **Green** | Updated existing data | (0.0, 0.5, 0.0) | Corrections, filled-in blanks, replaced placeholders for the same applicant |
| 🔵 **Blue** | New entity-specific information | (0.0, 0.4, 0.8) | When duplicating a template doc for a different applicant (e.g. Satvik-specific details) |

## Implementation via Docs API

```python
from tools.gws_auth import build_service
docs_svc = build_service('docs', 'v1')

# Read document to get text element indices
doc = docs_svc.documents().get(documentId=DOC_ID).execute()
content = doc.get('body', {}).get('content', [])

# Build color update requests
color_reqs = []
for el in content:
    if 'paragraph' in el:
        for elem in el['paragraph'].get('elements', []):
            tr = elem.get('textRun', {})
            if tr.get('content') and 'TARGET_TEXT' in tr['content']:
                start_idx = elem.get('startIndex')
                end_idx = elem.get('endIndex')
                if start_idx and end_idx:
                    color_reqs.append({
                        'updateTextStyle': {
                            'range': {'startIndex': start_idx, 'endIndex': end_idx},
                            'textStyle': {
                                'foregroundColor': {
                                    'color': {'rgbColor': {'red': 0.0, 'green': 0.5, 'blue': 0.0}}
                                }
                            },
                            'fields': 'foregroundColor'
                        }
                    })

# Apply in batches of 10
for i in range(0, len(color_reqs), 10):
    batch = color_reqs[i:i+10]
    docs_svc.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': batch}
    ).execute()
```

## When to use
- Multiple documents created from a shared template (e.g. Section 281 applications for different applicants)
- Incremental updates where the reviewer needs to see what changed since last review
- Handoff to a colleague who needs to verify edits before signing

## When NOT to use
- Final execution/signing versions (remove color, use plain black)
- Documents with complex table formatting (colored text may not render well)
- Very long documents with many small changes (use a change summary instead)

## Worked example (Jun 2026)
Three Section 281 applications for DRA KAAJ:
- **App 1** (Ashok Kumar — Palya + Byadarahalli): Green highlights on filled fields (PAN, address, phone, email, CIN, ITR data)
- **App 2** (Ashok Kumar — Byadarahalli only): Green on property scope changes
- **App 3** (Satvik Developers — Byadarahalli): Blue highlights on all Satvik-specific fields (different PAN, address, ITR)
