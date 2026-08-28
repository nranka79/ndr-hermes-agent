# Docs API — Section Replacement with Index Tracking

Replace a substantive section of a Google Doc (not just a placeholder word/phrase) with completely new content of different length, with per-line formatting (bold project names, italic entity lines, normal descriptions).

## Pattern

```
index = SECTION_START  # after deleteContentRange
→ insertText(\nProject Name\n)    → updateTextStyle(bold) on [index+1, index+1+len(name)]
   index += len(name) + 2
→ insertText(Entity: X\n)         → updateTextStyle(italic, grey) on [index, index+len(entity)]
   index += len(entity) + 1
→ insertText(Description\n)
   index += len(desc) + 1
```

## Step-by-step

### 1. Find the section boundaries

Read the doc, find the startIndex of the heading just before the section, and the endIndex of the paragraph just after:

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
content = doc.get('body', {}).get('content', [])
for el in content:
    if 'paragraph' in el:
        text = ''.join(e['textRun']['content'] for e in el['paragraph']['elements'] if 'textRun' in e)
        start, end = el.get('startIndex'), el.get('endIndex')
```

### 2. Delete the old content

```python
requests = [{
    "deleteContentRange": {
        "range": {"startIndex": SECTION_START, "endIndex": SECTION_END}
    }
}]
```

`endIndex` is exclusive — delete up to but not including the start of the next section you want to preserve.

### 3. Insert new formatted content

After the delete, `SECTION_START` is still the insertion point. Track `insert_index` for every subsequent insert:

```python
insert_index = SECTION_START

for np in new_projects:
    # Bold project name
    requests.append({"insertText": {
        "location": {"index": insert_index},
        "text": f"\\n{np['name']}\\n"
    }})
    requests.append({"updateTextStyle": {
        "range": {
            "startIndex": insert_index + 1,
            "endIndex": insert_index + 1 + len(np['name'])
        },
        "textStyle": {"bold": True},
        "fields": "bold"
    }})
    insert_index += len(np['name']) + 2

    # Entity line (italic, grey)
    requests.append({"insertText": {
        "location": {"index": insert_index},
        "text": f"{np['entity']}\\n"
    }})
    requests.append({"updateTextStyle": {
        "range": {
            "startIndex": insert_index,
            "endIndex": insert_index + len(np['entity'])
        },
        "textStyle": {
            "italic": True,
            "foregroundColor": {"color": {"rgbColor": {"red": 0.3, "green": 0.3, "blue": 0.3}}}
        },
        "fields": "italic,foregroundColor"
    }})
    insert_index += len(np['entity']) + 1

    # Description line (normal text, no formatting needed)
    requests.append({"insertText": {
        "location": {"index": insert_index},
        "text": f"{np['desc']}\\n"
    }})
    insert_index += len(np['desc']) + 1
```

### 4. Execute

```python
body = {"requests": requests}
resp = docs.documents().batchUpdate(documentId=DOC_ID, body=body).execute()
```

### 5. Verify

```python
updated = docs.documents().get(documentId=DOC_ID).execute()
```

## Pitfalls

### `fontSize` requires a Dimension object

The Google Docs API `fontSize` field expects a **Dimension object** (`{"magnitude": 11, "unit": "PT"}`), not a raw number. Passing a plain integer like `"fontSize": 11` gives a 400 error. For inline section replacements, bold/italic/color are sufficient — skip fontSize.

### Index tracking after deleteContentRange

After `deleteContentRange` removes content, insertIndex at SECTION_START becomes valid. Every subsequent `insertText` shifts remaining content forward. Track `insert_index` as a running variable advancing by each segment's length.

The `updateTextStyle` ranges are evaluated at each request's sequential execution context within the batch, not the final document state — so ranges computed from the running index are correct.

### Section boundary preservation

Ensure the delete range does NOT include the section heading you want to keep, and the insert text does NOT include trailing content belonging to the next section.