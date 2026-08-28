# Google Docs API — Document Inspection, Duplication & File Delivery

## When to use

- User shares a Google Doc link and you need to understand its structure (paragraphs, tables, images)
- User asks you to modify a doc but wants you to work on a copy first
- You created a PDF locally but the user can't download it via MEDIA tag — need a Drive link

## 1. Reading Document Structure

### List all content elements

The Docs API returns the document body as a flat list of content elements. Each element has one of: `paragraph`, `table`, `sectionBreak`, `tableOfContents`.

```python
from tools.gws_auth import build_service
docs = build_service('docs', 'v1')
doc = docs.documents().get(documentId=DOC_ID).execute()

body = doc.get('body', {}).get('content', [])
for i, elem in enumerate(body):
    if 'paragraph' in elem:
        text = ''
        for p_elem in elem['paragraph'].get('elements', []):
            if 'textRun' in p_elem:
                text += p_elem['textRun'].get('content', '')
            if 'inlineObjectElement' in p_elem:
                obj = p_elem['inlineObjectElement']
                text += f'[IMAGE: {obj["inlineObjectId"]}]'
        print(f'[{i}] PARA: "{repr(text)[:200]}"')
    elif 'table' in elem:
        rows = elem['table'].get('tableRows', [])
        print(f'[{i}] TABLE: {len(rows)} rows')
    elif 'sectionBreak' in elem:
        print(f'[{i}] SECTION BREAK')
```

### Find inline images

Inline images are embedded in paragraphs as `inlineObjectElement`. Their metadata (content URI, description) is in `doc['inlineObjects']`:

```python
if 'inlineObjects' in doc:
    for obj_id, obj in doc['inlineObjects'].items():
        props = obj['inlineObjectProperties']['embeddedObject']['imageProperties']
        print(f'Image: {obj_id}')
        print(f'  URI: {props.get("contentUri", "N/A")[:80]}...')
        print(f'  Description: {props.get("description", "N/A")}')
```

Key pixel positions:
- Each element has `startIndex` and `endIndex` for range operations
- Images have `startIndex`/`endIndex` at the paragraph element level
- `paragraph.startIndex` may be `None` for some elements — check the child element indices instead

### Read Google Doc content as text

For extracting the full text content of a Google Doc (not just structure):

```python
docs = build_service('docs', 'v1')
doc_content = docs.documents().get(documentId=DOC_ID).execute()
body = doc_content.get('body', {}).get('content', [])
text = ''
for elem in body:
    if 'paragraph' in elem:
        for p_elem in elem['paragraph'].get('elements', []):
            if 'textRun' in p_elem:
                text += p_elem['textRun'].get('content', '')
print(text[:2000])
```

## 2. Duplicating a Google Doc

When the user says "make a copy first, don't touch the original":

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

copied = drive.files().copy(
    fileId=ORIGINAL_DOC_ID,
    body={
        'name': 'OriginalName - COPY',
        'parents': []  # Omit to place in root; specify folder ID to place elsewhere
    },
    fields='id, name, webViewLink'
).execute()

print(f'Copy ID: {copied["id"]}')
print(f'Copy Link: {copied["webViewLink"]}')
```

**Important:** The `parents` field is optional. If omitted, the copy goes to the Drive root. To place it in a specific folder, pass `'parents': [FOLDER_ID]`.

Always share the copy link with the user first so they know where you're working.

## 3. Creating a New Google Doc from Scratch

When you need to create a brand new document in the user's Drive (not duplicate an existing one):

```python
from tools.gws_auth import build_service

docs = build_service('docs', 'v1')
new_doc = docs.documents().create(body={
    'title': 'Document Title Here'
}).execute()

new_doc_id = new_doc['documentId']
print(f"URL: https://docs.google.com/document/d/{new_doc_id}/edit")
```

### Populating a new doc with text

The new document starts empty. Use `batchUpdate` with `insertText` at the `endOfSegmentLocation`:

```python
CONTENT = """Section 1

Line 1
Line 2

Section 2
Line 3"""

requests = [
    {
        'insertText': {
            'endOfSegmentLocation': {},
            'text': CONTENT
        }
    }
]

result = docs.documents().batchUpdate(
    documentId=new_doc_id,
    body={'requests': requests}
).execute()
```

**Limitations:**
- The Docs API structures content by `startIndex`/`endIndex`. The first insert goes at index 1 (position 0 is reserved). Subsequent inserts can target specific indices.
- `endOfSegmentLocation: {}` appends to the end of the document body segment.
- To apply formatting (bold, headings, font size), add `updateParagraphStyle` requests to the same `batchUpdate` call, targeting the correct `startIndex`–`endIndex` range.
- For rich formatting, insert plain text first then apply styles — it's simpler than trying to interleave text+format requests.

### Verifying content was written

```python
doc = docs.documents().get(documentId=new_doc_id).execute()
text = ''
for element in doc['body']['content']:
    if 'paragraph' in element:
        for e in element['paragraph'].get('elements', []):
            if 'textRun' in e:
                text += e['textRun'].get('content', '')
print(f"Verified: {len(text)} chars written")
```

## 4. File Delivery — MEDIA tag fallback to Drive

When a user can't download a file sent via `MEDIA:/path` (Telegram may not show it, or the download fails), upload to Drive with public permissions:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')

# Upload
media = MediaFileUpload('/tmp/file.pdf', mimetype='application/pdf', resumable=True)
uploaded = drive.files().create(
    body={'name': 'file.pdf'},
    media_body=media,
    fields='id, name, webViewLink'
).execute()

# Make public
perm = {'type': 'anyone', 'role': 'reader'}
drive.permissions().create(fileId=uploaded['id'], body=perm).execute()

# Share link
link = f"https://drive.google.com/file/d/{uploaded['id']}/view"
print(f'Link: {link}')
```

**Pattern:** always try MEDIA first (it's instant), fall back to Drive upload only if the user reports they can't download.

## 5. Adding Comments (Alternative to Suggested Edits)

The Docs API **cannot create suggested edits/tracked changes**. If a user wants changes shown as suggestions rather than direct edits, use the Drive API comments as a workaround:

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')

comment = drive.comments().create(
    fileId=DOC_ID,
    body={
        'content': '[Suggestion] Explain the proposed change here — '
                    'e.g. "Split 50/50: Anbu gets ₹X, team gets ₹Y"'
    },
    fields='id,content'
).execute()

print(f"Comment created: {comment['id']}")
```

**Behaviour:**
- Comments appear above the document, not inline as tracked changes
- They appear as from the user whose OAuth token is used
- To remove a comment: `drive.comments().delete(fileId=DOC_ID, commentId=COMMENT_ID).execute()`
- To list all comments: `drive.comments().list(fileId=DOC_ID).execute()`

**When to use comments vs. direct edits:**

| User asks for... | What to do |
|---|---|
| "Edit the document" | Use docs.batchUpdate (direct edits) |
| "Suggest changes" / "suggesting mode" | Use drive.comments().create() — explain API limitation |
| "Add this to the doc" | Direct edit via batchUpdate |
| "Review my doc and make suggestions" | Comments with the proposed changes |

## Pitfalls

- **Docs API doesn't create docs with parent folders** — use Drive API `files().create()` with `mimeType='application/vnd.google-apps.document'` and `parents[]`, then Docs API for content
- **`inlineObjects` key may be missing** from the doc dict if no images exist — check with `if 'inlineObjects' in doc:` before iterating
- **File.copy() doesn't preserve permissions** — the copy inherits the copier's default permissions (usually private). Set `'anyone' reader` explicitly if you need public access
- **Drive API rate limits** — sequential uploads only for files >1MB; parallel uploads cause timeouts
- **`files.get_media` for Google-native docs (Docs/Sheets/Slides)** raises `HttpError 403` — use `files.export_media(mimeType='application/pdf')` instead
- **MEDIA tag delivery** works for most users but may fail if the Telegram client doesn't support inline file delivery. The Drive link fallback is universal.
