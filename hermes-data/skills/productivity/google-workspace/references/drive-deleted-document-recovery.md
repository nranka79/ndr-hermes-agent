# Drive: Deleted / Missing Document Recovery

Multi-source search workflow when a known document ID returns 404, or the
user says "open the X document" and it isn't where expected. Covers tracing
the document through email, session history, and local backups.

## When to Use This

- A known Google Doc / file ID returns `HttpError 404` (deleted or moved)
- User says "open the document you created/uploaded/signed" and it's not
  in the expected Drive folder
- User refers to a document by description/parties/topic rather than filename
- Need to reconstruct what happened to a document after it was created

## Phase 1: Identify the Document

Before searching, nail down:

- **What was it?** (Google Doc, PDF, DOCX — signature-block agreement, sharing
  agreement, letter — who were the parties?)
- **When was it created/last seen?** (approximate date range)
- **What was the workflow?** (was it eSigned? emailed? printed? couriered?)
- **What email thread discussed it?** (who was involved? subject line clues)

If the user gives you a description ("Ranka Amber Sharing agreement with
Raghu Iyer and DRE Realty"), use that to search session history **first**:

```
session_search(query="Ranka Amber Raghu Iyer sharing agreement", limit=3)
```

Session history often contains the exact Google Doc ID, file upload events,
and signing workflow details.

## Phase 2: Trace via Email

### 2a. Find the email thread

Search Gmail for the parties or subject matter:

```python
from tools.gws_auth import build_service
svc = build_service('gmail', 'v1', service_name='google-draas')

results = svc.users().messages().list(
    userId='me',
    q='subject:"Ranka Amber" "sharing agreement"'
).execute()
```

### 2b. Extract Google Doc links from email body

Emails often contain links to Google Docs (shared via "Anyone with link").
Extract these from the message body:

```python
import base64, re

msg = svc.users().messages().get(userId='me', id=MESSAGE_ID, format='full').execute()

def extract_doc_links(part):
    """Recursively extract docs.google.com links from email parts."""
    links = []
    if 'parts' in part:
        for p in part['parts']:
            links.extend(extract_doc_links(p))
    elif part['mimeType'] == 'text/html':
        data = part['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            links = re.findall(
                r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+', body
            )
    return links

doc_links = extract_doc_links(msg['payload'])
```

### 2c. Attempt to access each link

```python
for link in set(doc_links):
    doc_id = link.split('/d/')[1].split('/')[0].split('?')[0]
    try:
        doc = svc.files().get(fileId=doc_id, fields='id, name, trashed').execute()
        print(f"✅ {doc_id} → {doc['name']} (trashed={doc.get('trashed', False)})")
    except Exception as e:
        print(f"❌ {doc_id} → {e}")
```

A 404 means the doc was permanently deleted. Check the `trashed` field —
if `trashed=True`, it can be restored via the Drive UI or `files().update()`.

### 2d. Check email attachments

The thread may contain a signed/executed PDF as an attachment. Walk all
parts of all messages:

```python
for msg in thread.get('messages', []):
    parts = [msg['payload']]
    while parts:
        part = parts.pop(0)
        if 'parts' in part:
            parts.extend(part['parts'])
        if part.get('filename') and part.get('mimeType') == 'application/pdf':
            # Check if it matches the agreement
            fname = part['filename'].lower()
            if any(kw in fname for kw in ['ssa', 'supplement', 'sharing',
                                          'agreement', 'execute', 'sign',
                                          'amber']):
                # Save it
                att = svc.users().messages().attachments().get(
                    userId='me', messageId=msg['id'],
                    id=part['body']['attachmentId']
                ).execute()
                data = base64.urlsafe_b64decode(att['data'])
                with open(f'/tmp/{part["filename"]}', 'wb') as f:
                    f.write(data)
```

## Phase 3: Search the Gmail Drafts (if Hermes created one)

If Hermes drafted an email that attached or referenced the document, check
the drafts folder:

```python
drafts = svc.users().drafts().list(userId='me').execute()
for d in drafts.get('drafts', []):
    dmsg = svc.users().drafts().get(userId='me', id=d['id'],
                                     format='full').execute()
    # Check body for doc links or attachments
```

## Phase 4: Search Drive with Multiple Queries

Use at least these query families:

| Query Purpose | Example |
|---|---|
| Exact filename | `name = 'Ranka Amber SSA.docx'` |
| Partial name | `name contains 'Sharing' and name contains 'Amber'` |
| Content search | `fullText contains 'Supplementary Sharing Agreement'` |
| Date range | `modifiedTime > '2026-06-01T00:00:00'` |
| Folder contents | `'FOLDER_ID' in parents` |
| Trash | `trashed = true` |

```python
# Check trash explicitly
results = svc.files().list(
    q="name contains 'Amber' and trashed = true",
    spaces='drive',
    pageSize=50,
    fields='files(id, name, trashed)'
).execute()
```

## Phase 5: Search Local File System

Hermes may have created local copies (DOCX, MD outlines). Check:

```bash
find /data/hermes/cron/output/ -iname '*ranka*amber*' -type f
find /data -maxdepth 5 -iname '*SSA*' -type f
find /opt/hermes/hermes-data -iname '*sharing*agreement*' 2>/dev/null
```

Local copies are typically **pre-signing drafts**. The signed/executed version
is usually only on Drive or emailed as a PDF.

## Phase 6: Search Session History

Use session_search for document creation/upload events:

```
session_search(query="uploaded Ranka Amber sharing agreement signed")
session_search(query="SSA supplementary sharing agreement ranka amber")
```

Session history often records the exact Drive file ID, upload command,
and sharing settings applied.

## Phase 7: Cross-reference with Known Document IDs

If session history reveals document IDs but they return 404, the document
was permanently deleted. Cross-reference against:

- The Google Doc ID from session history (e.g. `1EnY77qQ-UXeMV7Pr49l6kiK...`)
- DOCX/MD files in `/data/hermes/cron/output/` (draft versions)
- Email body links (forwarded messages may contain the same link)

## What to Present to the User

If the document is truly missing:

1. **What was found** — document name, parties, date range, Google Doc ID
2. **What happened** — the document was deleted (404) or not uploaded
3. **What exists** — draft DOCX/MD versions available on the local system
   (pre-signing), related emails, related Drive documents (JDA, GPA, etc.)
4. **Options** — reconstruct from the last draft and re-initiate signing,
   or check if the signed copy is on the user's personal device

If you find the document:

1. **Present the link** directly
2. **Describe the document** — name, date, parties, what stage (draft/signed)
3. **Note any discrepancies** — if what you found doesn't match the user's
   description, flag it

## Pitfalls

- **Google Doc deleted = can't recover via API.** Only the user can check
  their Drive Trash in the Drive UI (web or mobile) and restore it. The API
  can detect trash but can't see files that were permanently deleted.
- **Local DOCX files are drafts, not the signed version.** The eSigned PDF
  lives on the signing platform (eMudhra/SignDesk) or was downloaded to the
  user's device — it's rarely on the Drive unless explicitly uploaded.
- **Don't loop 15+ searches without updating the user.** After 3-4 rounds of
  searching, present what you've found and ask for more specific guidance
  (folder name, someone who might have moved it, etc.).
- **Email links may be stale.** Forwarded messages share the same Google Doc
  ID — if it was deleted after sharing, the link dies for everyone.
- **Beware of "file not found" on shared drives** — use `supportsAllDrives=True`
  and `corpora='allDrives'` when the file might be in a Shared Drive:
  ```python
  f = svc.files().get(fileId=..., supportsAllDrives=True).execute()
  ```
