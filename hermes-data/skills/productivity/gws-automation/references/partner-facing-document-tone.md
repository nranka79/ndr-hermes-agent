# Partner-Facing Document Tone & Collaboration Merge

Class of work: Revising an existing partnership/discussion document by incorporating feedback from a collaborator — then producing a version that will be shared with external partners.

## When this applies

- User has a draft document (risk analysis, discussion note, term sheet) that will be shared with external partners
- A collaborator (spouse, colleague, advisor) has provided separate feedback notes
- User wants the new version to feel **collaborative, not demanding** — especially when it contains provisions that give one party structural control

## Workflow

### 1. Locate the feedback document

Collaborators may provide feedback as:
- A **separate Google Doc** in the user's Drive (search by owner email or name)
- Comments on the original document (use Drive Comments API)
- Email to the user (search Gmail by sender)
- Direct message in Telegram (search session history)

Drive search pattern for a collaborator's feedback doc:
```python
drive = build_service('drive', 'v3')
results = drive.files().list(
    q="fullText contains 'TerraGreens' or name contains 'Feedback'",
    spaces='drive',
    fields='files(id, name, owners, createdTime)',
    pageSize=50
).execute()
# Check owners for the collaborator's email
```

### 2. Read both source docs

Use Docs API to extract full text:
```python
docs = build_service('docs', 'v1')
doc = docs.documents().get(documentId=DOC_ID).execute()
text = ''
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        for p_elem in elem['paragraph'].get('elements', []):
            if 'textRun' in p_elem:
                text += p_elem['textRun'].get('content', '')
```

### 3. Merge with tone rules

When the revised document will go to external partners, apply these rules:

| Rule | Example |
|------|---------|
| **Frame control provisions as structural necessity** | "51% is not about control — it's because DRA needs consolidation rights for its IPO/merger path" |
| **End each section with an invitation** | "*Question to partners: What do you think? Open to alternatives.*" |
| **Use softeners for sensitive terms** | "Suggested approach", "Open for discussion", "If partners have alternative suggestions..." |
| **Name all parties symmetrically** | Avoid singling out one partner's entities — name everyone's explicitly |
| **Explain 'why', not just 'what'** | For every potentially contentious clause, add a paragraph explaining why it exists |
| **Flag drafting failures** | "If any item reads as targeting a specific partner, that is a drafting failure" |
| **Acknowledge it's a draft** | "This is a collaborative discussion note — not a final agreement" |

### 4. Decide: update in-place vs create D2

Ask yourself: are the changes structural enough (new ratio, new sections, different tone) that updating in-place would make it hard to track? If yes, create a new version with a suffix (e.g., `_D2`). Use `markdown-to-google-doc-import` for clean initial creation.

### 5. Upload via Drive API import

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')
media = MediaFileUpload("/tmp/draft.md", mimetype="text/markdown")
uploaded = drive.files().create(
    body={
        "name": "YYYYMMDD_Project_DocumentType_D2",
        "mimeType": "application/vnd.google-apps.document",
        "parents": [FOLDER_ID]
    },
    media_body=media,
    fields="id, name, webViewLink"
).execute()
```

### 6. Verify content

After upload, check that all sections rendered:
```python
docs = build_service('docs', 'v1')
doc = docs.documents().get(documentId=uploaded['id']).execute()
headings = []
for elem in doc['body']['content']:
    style = elem.get('paragraph', {}).get('paragraphStyle', {}).get('namedStyleType', '')
    if 'HEADING' in style:
        for p_elem in elem['paragraph'].get('elements', []):
            if 'textRun' in p_elem:
                headings.append(f"[{style}] {p_elem['textRun']['content'].strip()}")
# Verify all expected sections present
```

## Common pitfalls

1. **Markdown tables** lose formatting on import — if your document has tables, either: (a) keep them simple pipe tables that survive, or (b) note to the user that the table needs reformatting in the Doc
2. **Tone contradiction** — a document that opens with "this is collaborative" but has aggressive language in sections reads as manipulative. Every section must carry the same cooperative tone
3. **False symmetry** — if you name all three partners' entities, make sure the obligations are genuinely symmetrical, not just the label
4. **The 51% explanation matters more than the number** — a well-explained 51% is less threatening than a 50.1% with no explanation. Lead with the *why* (IPO/merger readiness), not the *what* (control)
5. **Missing 'open questions' section** — always include an explicit "What have we missed?" section at the end so partners feel their input is genuinely solicited
