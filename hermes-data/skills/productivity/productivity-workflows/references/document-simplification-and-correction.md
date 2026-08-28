# Document Simplification & Correction Workflow

## When to use

- User shares a Google Doc and says "simplify this" / "too verbose" / "make it shorter"
- User identifies calculation errors, incorrect assumptions, or logic flaws in a document
- User wants a corrected version delivered as a new Google Doc (never edit the original without permission)

## Workflow

### Step 1: Read the full document

```python
from tools.gws_auth import build_service
docs = build_service('docs', 'v1')
doc = docs.documents().get(documentId=DOC_ID).execute()
text = ''
for element in doc['body']['content']:
    if 'paragraph' in element:
        for e in element['paragraph'].get('elements', []):
            if 'textRun' in e:
                text += e['textRun'].get('content', '')
```

Print the full text to identify:
- Structure (sections, subsections)
- Where the verbosity is (preamble, explanatory paragraphs, repeated points)
- All numbers, calculations, and percentage splits

### Step 2: Identify what to simplify

Common patterns the user complains about:
- **Preamble/essay text** — mission statements, philosophy, "this is a discussion document" boilerplate. Strip to 1–2 sentences max.
- **Repeated explanations** — same concept explained differently in multiple sections. Keep one.
- **Excessive bullet depth** — 4+ sub-levels of bullets. Flatten to 2 levels.
- **Long rationale paragraphs** — replace with a single sentence or delete entirely.
- **Over-explained examples** — keep the numbers, remove the narrative around them.

### Step 3: Verify and fix calculations

Before writing the new version, independently verify every calculation:

1. **Check each number**: Does the arithmetic make sense? (e.g., 1% of ₹8 Cr = ₹8,00,000 not ₹0.08)
2. **Check splits**: If the user says "this is wrong — it's 50/50 not 100/0", apply the correction to every scenario/example
3. **Check units**: Mixed crore/lakh notation? Standardise to lakhs or full INR
4. **Check percentages**: % of what? % of fixed pay? % of total? Be explicit

Common errors found in incentive/compensation docs:
- 100% of incentive attributed to one person when it should be split with a team
- Crore/lakh notation mixed in the same calculation line
- ₹0.08 (meaning ₹0.08 Cr = ₹8,00,000) written without the Cr marker, making it look like ₹0.08

### Step 4: Create a NEW document (never edit original)

```python
# Create
new_doc = docs.documents().create(body={
    'title': 'Original Title - Simplified v2'
}).execute()
new_id = new_doc['documentId']

# Populate
CONTENT = """simplified content here"""
docs.documents().batchUpdate(
    documentId=new_id,
    body={'requests': [{'insertText': {'endOfSegmentLocation': {}, 'text': CONTENT}}]}
).execute()
```

### Step 5: Deliver the link

```python
share_url = f"https://docs.google.com/document/d/{new_id}/edit"
```

Present what changed:
- What was simplified
- What was corrected (with before/after comparison for calculations)
- The final numbers

## Pitfalls

- **Never edit the original document** — always create a new one. The user will say "share back" meaning a new doc.
- **Verification timeout**: `execute_code` may time out when printing very long doc content. Read in chunks or check key markers only.
- **Number formatting**: Google Docs inserts auto-formatting for lists (bullets, numbering). Plain text insert works fine but numbered lists won't auto-number. Use explicit numbers in the text content.
- **Table preservation**: The Docs API `batchUpdate` + `insertText` does NOT create tables. If the original has tables you need to preserve, either: (a) convert table data to structured text in the simplified version, or (b) use the Docs API table insertion requests (more complex).
- **User corrections are first-class signals**: If the user says "this calculation is wrong", the correction is not optional. Fix it before delivering. Do not present the fix as a suggestion.

## Example: Correction pattern

**Before (original):**
```
Timeline incentive: 1.0% of ₹8 Cr = ₹0.08
Total Incentive: ₹300,000.19
Incentive split: Anbu gets 100% → Percentage of fixed pay: 14.3%
```

**After (corrected):**
```
Timeline incentive: 1.0% × ₹8,00,00,000 = ₹8,00,000
Total Incentive Pool = ₹21,50,000
Split: → Anbu (50%): ₹10,75,000 → Team Pool (50%): ₹10,75,000
Anbu's % of fixed pay: 51.2%
```
