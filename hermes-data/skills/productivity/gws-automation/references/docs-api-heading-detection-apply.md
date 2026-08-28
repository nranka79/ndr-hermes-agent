# Detecting and Applying Heading Styles via Docs API

Google Docs API does not have a "select all" or "apply named style to matching elements" operation. Named styles must be applied per-paragraph using `updateParagraphStyle`. This reference covers how to reliably detect headings by content pattern and apply `TITLE`, `HEADING_1`, `HEADING_2`, and `HEADING_3` styles.

## Why named styles matter

Documents that use raw formatting (manual bold + larger font) instead of named styles:
- Don't appear in the document outline / table of contents
- Can't be globally restyled
- Export inconsistently to PDF
- Fail accessibility checks

Named styles (`TITLE`, `HEADING_1`, `HEADING_2`, `HEADING_3`) fix all of these.

## Step 1: Set style definitions first

Before applying per-paragraph styles, set the document's named style definitions. The Docs API lets you update a style definition by applying property changes to any range with that `namedStyleType`:

```python
# This updates the global HEADING_1 definition
requests.append({
    'updateParagraphStyle': {
        'range': {'startIndex': 1, 'endIndex': 2},  # arbitrary range
        'paragraphStyle': {
            'namedStyleType': 'HEADING_1',
            'alignment': 'START',
            'spaceAbove': {'magnitude': 18, 'unit': 'PT'},
            'spaceBelow': {'magnitude': 6, 'unit': 'PT'},
            'lineSpacing': 115,
        },
        'fields': 'namedStyleType,alignment,spaceAbove,spaceBelow,lineSpacing'
    }
})
requests.append({
    'updateTextStyle': {
        'range': {'startIndex': 1, 'endIndex': 2},
        'textStyle': {
            'bold': True,
            'fontSize': {'magnitude': 16, 'unit': 'PT'},
            'weightedFontFamily': {'fontFamily': 'Arial'},
        },
        'fields': 'bold,fontSize,weightedFontFamily'
    }
})
```

Do this for: `TITLE`, `HEADING_1`, `HEADING_2`, `HEADING_3`, and `NORMAL_TEXT`. Setting the definition once means every paragraph you later tag with that style automatically gets the right formatting.

## Step 2: Classify headings by content pattern

Read the document body and classify each non-empty paragraph:

```python
import re

H1_PATTERNS = [
    re.compile(r'^Part\s+(I|II|III|IV|V|VI)\s*[—\-–]'),  # "Part I — ..."
    re.compile(r'^Briefing Note'),
    re.compile(r'^\d+\.\s+[A-Z]'),  # "1. PARTNERSHIP", "2. CAPITAL"
    re.compile(r'^POTENTIAL RISKS'),
    re.compile(r'^NEXT STEPS'),
    re.compile(r'^[A-Z]{4,}'),  # All-caps short lines like "NEXT STEPS"
]

H2_PATTERNS = [
    re.compile(r'^[A-Z]\.\s+[A-Z]'),  # "A. Ownership", "B. Takeover Right"
    re.compile(r'^\d+\.\d+\s'),  # "1.1 Clearly Defined"
]

H3_PATTERNS = [
    re.compile(r'^A note on the'),
    re.compile(r'^The goal:'),
    re.compile(r'^Three principles'),
]

classified = {}
for i, elem in enumerate(body):
    para = elem.get('paragraph', {})
    if not para:
        continue
    texts = []
    for seg in para.get('elements', []):
        tr = seg.get('textRun', {})
        if tr and 'content' in tr:
            texts.append(tr['content'])
    full_text = ''.join(texts).strip()
    if not full_text:
        continue

    # Title (first line of document)
    if 'Discussion_Note_V4' in full_text or 'Discussion Note' in full_text:
        classified[i] = 'TITLE'
        continue

    # H1 first
    for pat in H1_PATTERNS:
        if pat.match(full_text):
            classified[i] = 'HEADING_1'
            break
    else:
        # H2
        for pat in H2_PATTERNS:
            if pat.match(full_text):
                classified[i] = 'HEADING_2'
                break
        else:
            # H3
            for pat in H3_PATTERNS:
                if pat.match(full_text):
                    classified[i] = 'HEADING_3'
                    break
```

**Watch out for false positives:** `^\d+\.\s+[A-Z]` matches numbered list items like "1. Profit share can be asymmetric..." — these are body text, not headings. Filter by text length or check if the text ends with a period (list items end with periods, headings don't).

## Step 3: Apply in one batch

```python
heading_reqs = []
for idx, cls in sorted(classified.items()):
    elem = body[idx]
    start = elem.get('startIndex', 1)
    end = elem.get('endIndex', start + 1)
    heading_reqs.append({
        'updateParagraphStyle': {
            'range': {'startIndex': start, 'endIndex': end},
            'paragraphStyle': {'namedStyleType': cls},
            'fields': 'namedStyleType'
        }
    })

# Apply in batches of 40
for i in range(0, len(heading_reqs), 40):
    chunk = heading_reqs[i:i+40]
    docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': chunk}).execute()
```

**Note:** This only sets the `namedStyleType` property. The actual font/size/spacing comes from the style definition set in Step 1. To apply per-paragraph overrides, add separate requests for font/size/bold to `updateTextStyle`.

## Step 4: Fix misclassified headings

After the batch apply, check for false positives. Common ones:

| False positive pattern | Fix |
|-----------------------|-----|
| `1. Item text...` under a list/principle section | Revert to `NORMAL_TEXT` |
| Short bullet-like lines starting with a number | Revert to `NORMAL_TEXT` |
| All-caps short text that's actually a label | Check if it's followed by body text on the same element |

Fix these by reapplying `NORMAL_TEXT` to the affected elements.

## Recommended heading style values (GPT 5.5 design system)

| Style | Font | Size | Weight | Alignment | Space above | Space below |
|-------|------|------|--------|-----------|-------------|-------------|
| TITLE | Arial | 20pt | Bold | Center | 0pt | 12pt |
| HEADING_1 | Arial | 16pt | Bold | Left | 18pt | 6pt |
| HEADING_2 | Arial | 13pt | Bold | Left | 12pt | 4pt |
| HEADING_3 | Arial | 11.5pt | Bold | Left | 8pt | 3pt |
| NORMAL_TEXT | Arial | 10.5pt | Regular | Left | 0pt | 6pt |

Line spacing for all: 1.15 (API value: 115)
