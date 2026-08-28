# Document Consolidation — Digest Source Into Main Analysis

Class of work: User provides a short source document (summary, feedback note, possession analysis) and wants its contentions fully absorbed into a larger existing analysis document, then the source deleted.

## When this applies

- A small source doc exists (under 500 chars or a few paragraphs) with key contentions/claims
- A larger main analysis document already covers the topic (e.g., title analysis report)
- User wants the source's claims integrated — not as a separate doc, but as a structured supplement inside the main doc
- User then wants the source document deleted (it served its purpose)

## The pipeline

```
Read source doc with Docs API (get full text)
  └─ Identify each contention/claim as structured sections
  └─ Append to main analysis doc as a new Supplement section
  └─ Delete the source doc
  └─ Report what was added
```

## Step 1 — Read the source document

```python
from tools.gws_auth import build_service

docs = build_service('docs', 'v1')
doc = docs.documents().get(documentId=SOURCE_DOC_ID).execute()

text = ''
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        for p_elem in elem['paragraph'].get('elements', []):
            if 'textRun' in p_elem:
                text += p_elem['textRun'].get('content', '')
```

## Step 2 — Parse contentions

Short source docs often contain 3-5 numbered or bulleted claims. Extract each as a standalone "Contention" with:
- **The claim** (quote or paraphrase)
- **The counter-argument** (what the main analysis already says about it)
- **Verification actions** (what to check to confirm or refute the claim)

## Step 3 — Append to the main document

Find the end of the main document, then insert a new supplement section:

```python
# Get end index from last element
doc = docs.documents().get(documentId=MAIN_DOC_ID).execute()
body = doc.get('body')
content = body.get('content', [])
end_index = content[-1].get('endIndex', 1)

# Build the supplement text with structured formatting
supplement = f"""
═══════════════════════════════════════════════════════════
SUPPLEMENT [N]: [TOPIC] (ADDED [DATE])
═══════════════════════════════════════════════════════════

[CONTENTION 1: Title]
─ [Key point 1]
─ [Key point 2]
─ [Key point 3]

[CONTENTION 2: Title]
...
"""

docs.documents().batchUpdate(
    documentId=MAIN_DOC_ID,
    body={'requests': [{
        'insertText': {
            'location': {'index': end_index - 1},
            'text': supplement
        }
    }]}
).execute()
```

## Step 4 — Delete the source document

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

try:
    drive.files().delete(fileId=SOURCE_DOC_ID).execute()
    print("✅ Deleted source document")
except:
    # Fallback: trash instead of permanent delete
    drive.files().update(fileId=SOURCE_DOC_ID, body={'trashed': True}).execute()
    print("✅ Trashed source document")
```

## Structure of a good supplement section

| Element | Example |
|---------|---------|
| **Contention header** | "CONTENTION 1: Narasamma obtained possession without any registered title deed" |
| **Bullet evidence** | "─ No sale deed from Trust to Narasamma exists in analyzed documents" |
| **Risk level** | "HIGH — If true, entire chain could collapse" |
| **Verification action** | "Obtain certified copy of Trust compromise — check trustee authority" |
| **Cross-reference** | "See Tier 1.1 of checklist below for verification steps" |

## Pitfalls

1. **Don't merge — append.** The source document's contentions should be added as a new section, not woven into existing text. This preserves auditability — the user can see what came from the source doc vs the original analysis.
2. **Include counter-points.** If the main analysis already addresses a claim, note it. Don't present the source doc's claims as unrefuted truth.
3. **Delete only after append succeeds.** Confirm the append took effect (re-read the main doc to verify) before deleting the source.
4. **Report what was added.** After deletion, tell the user exactly what was incorporated: "Added 3 contentions from your source doc, each with verification steps and risk levels."
5. **Short source docs are deceptive.** Even a 387-character doc can contain 3-4 distinct contentions that each warrant separate analysis. Don't treat brevity as simplicity.
