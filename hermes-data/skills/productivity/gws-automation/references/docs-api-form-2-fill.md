# Form 2 (Notice of Change in Constitution of a Firm) — Docs API Fill Workflow

Complete end-to-end workflow for filling an Indian Partnership Act Form 2 Google Doc using the Docs API. Covers all the techniques from `docs-api-tables.md` in a real session.

## Document Structure

Section 2 (Nature of Change) was a **4×4 table** with checkbox+label pairs. Section 4 (Partners) was a **3×7 table** with headers + two partner rows. Both contained pre-filled placeholder content (checkbox characters, underline text fillers).

## Step 1: Identify the authenticated user

The token on disk may belong to a different account than expected. Always verify:

```python
from tools.gws_auth import build_service
telegram_id = 'ndr'
drive = build_service('drive', 'v3', telegram_id)
about = drive.about().get(fields='user').execute()
authed_email = about['user']['emailAddress']
print(f"Token belongs to: {authed_email}")
# Compare to doc owner
meta = drive.files().get(fileId=DOC_ID, fields='owners, capabilities').execute()
owner = meta['owners'][0]['emailAddress']
can_edit = meta['capabilities']['canEdit']
print(f"Owner: {owner}, Can edit: {can_edit}")
```

If `canEdit: False` despite being the owner's token, the doc needs to be shared with the authed account's email as Editor.

## Step 2: Export and read the document

For publicly viewable docs, use the export URL instead of the Docs API:

```python
# No auth needed for export
import requests
doc_id = '1u0jUYUc08OPpUiX2nyguhd1Zvpx9kpDoo4iFaO8t5Yc'
resp = requests.get(f'https://docs.google.com/document/d/{doc_id}/export?format=txt')
print(resp.text)
```

Then use the Docs API to read the full structure with indices:

```python
docs = build_service('docs', 'v1', telegram_id)
doc = docs.documents().get(documentId=doc_id).execute()
content = doc.get('body', {}).get('content', [])

for elem in content:
    if 'table' in elem:
        for row in elem['table']['tableRows']:
            for cell in row['tableCells']:
                for ce in cell.get('content', []):
                    if 'paragraph' in ce:
                        for pe in ce['paragraph'].get('elements', []):
                            if 'textRun' in pe:
                                print(f"  ({pe['startIndex']},{pe['endIndex']}): {repr(pe['textRun']['content'])}")
```

## Step 3: Update checkboxes (☐ → ☑)

Checkbox cells contain a single Unicode character (☐ = U+2610) followed by `\n`. The textRun is always at `cell_startIndex + 1`:

```python
# Reading from doc dump:
# cell[2,2] at (786, 789): textRun (787, 789) = '☐\n'
# cell[3,0] at (822, 825): textRun (823, 825) = '☐\n'

# Process highest index first
requests = [
    {'deleteContentRange': {'range': {'startIndex': 823, 'endIndex': 824}}},
    {'insertText': {'location': {'index': 823}, 'text': '☑'}},
    {'deleteContentRange': {'range': {'startIndex': 787, 'endIndex': 788}}},
    {'insertText': {'location': {'index': 787}, 'text': '☑'}},
]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

## Step 4: Update partner details

### Father's name (unique string → replaceAllText)

```python
{'replaceAllText': {
    'containsText': {'text': 'S/o __________________', 'matchCase': True},
    'replaceText': 'S/o Mr. Ram Kumar'
}}
```

### Age (delete + insert, single paragraph cell)

Cell structure after father name update:
- cell[2,4] at (1580, 1586): textRun (1581, 1586) = '____\n'

```python
# Delete the underscores (not the \n), insert "55"
requests = [
    {'deleteContentRange': {'range': {'startIndex': 1581, 'endIndex': 1585}}},
    {'insertText': {'location': {'index': 1581}, 'text': '55'}}
]
```

### Address (multi-paragraph cell — re-fetch between steps)

Cell structure (two paragraphs, each ending with `\n`):
- Paragraph 0: (1526, 1553) '__________________________\n'
- Paragraph 1: (1553, 1580) '__________________________\n'

**Cannot** deleteContentRange across paragraphs. Delete one paragraph at a time:

```python
# Step 1: Delete second paragraph's underscores
docs.documents().batchUpdate(documentId=doc_id, body={'requests': [{
    'deleteContentRange': {'range': {'startIndex': 1553, 'endIndex': 1579}}
}]}).execute()

# Step 2: Re-fetch doc to get shifted indices
doc = docs.documents().get(documentId=doc_id).execute()
# After step 1: para 0 is now (1526, 1527) = '\n' (empty)
# 2nd para shifted to (1527, 1554) = '__________________________\n'

# Step 3: Delete second para's underscores now at new indices
docs.documents().batchUpdate(documentId=doc_id, body={'requests': [{
    'deleteContentRange': {'range': {'startIndex': 1527, 'endIndex': 1553}}
}]}).execute()

# Step 4: Delete empty first para
docs.documents().batchUpdate(documentId=doc_id, body={'requests': [{
    'deleteContentRange': {'range': {'startIndex': 1526, 'endIndex': 1527}}
}]}).execute()

# Step 5: Insert new address
docs.documents().batchUpdate(documentId=doc_id, body={'requests': [{
    'insertText': {'location': {'index': 1526},
     'text': 'B-27, Zonasha Paradise, Near Alpine Eco Apartment, Doddanekundi, Bengaluru – 560 037\n'}
}]}).execute()
```

**Alternative (single batch, all at once):** If you track index shifts precisely, you can do it in one batch:

```python
new_address = 'B-27, Zonasha Paradise, Near Alpine Eco Apartment, Doddanekundi, Bengaluru – 560 037\n'

requests = [
    # Step A: Delete 2nd para (higher index first — 1527 after Step 1 shift)
    {'deleteContentRange': {'range': {'startIndex': 1527, 'endIndex': 1553}}},
    # Step B: Delete empty 1st para
    {'deleteContentRange': {'range': {'startIndex': 1526, 'endIndex': 1527}}},
    # Step C: Insert new text
    {'insertText': {'location': {'index': 1526}, 'text': new_address}},
    # Step D: Now fix age (indices shifted again after address insert +92 chars)
    # Re-fetch needed to get correct age indices before inserting '55'
]
```

**In practice, re-fetching between edits is safer than tracking shifts across multiple operations in a batch.**

## Verification

After all edits, verify by reading the full document text and checking each field:

```python
full_text = ""
for elem in content:
    if 'paragraph' in elem:
        for pe in elem['paragraph'].get('elements', []):
            if 'textRun' in pe:
                full_text += pe['textRun'].get('content', '')
    elif 'table' in elem:
        for row in elem['table']['tableRows']:
            for cell in row['tableCells']:
                for ce in cell.get('content', []):
                    if 'paragraph' in ce:
                        for pe in ce['paragraph'].get('elements', []):
                            if 'textRun' in pe:
                                full_text += pe['textRun'].get('content', '')

checks = [
    "☑\nChange in profit-sharing ratio",
    "☑\nChange in capital contribution",
    "S/o Mr. Ram Kumar",
    "B-27, Zonasha Paradise",
    "55\n",
]
all(c in full_text for c in checks)
```

## Key Lessons

| Lesson | Detail |
|--------|--------|
| **Token != user** | Token on disk may belong to a different Google account than the chat user. Always `drive.about().get(fields='user')` to confirm. |
| **Cell +1 rule** | textRun.startIndex = cell.startIndex + 1, always. |
| **No cross-paragraph delete** | `deleteContentRange` cannot span paragraph boundaries in table cells. Edit each paragraph separately. |
| **Keep trailing \n** | Deleting the final `\n` of a paragraph triggers `"Invalid deletion range"`. |
| **replaceAllText is document-wide** | Verify uniqueness before using on table cell strings. |
| **Batch order: highest index first** | When batching multiple operations, process highest-index operations first to avoid cascade shifts. |
| **Re-fetch between multi-step edits** | Safer than tracking index shifts across 3+ operations in one batch. |
| **Checkbox chars are Unicode** | ☐ = U+2610, ☑ = U+2611. Replace by deleting+inserting the single character. |
