# Project Material Audit — Multi-Account Discovery & Inventory

**Scenario (Ranka Iris, 2026-08-28):** NDR wants to find ALL available materials (brochures, images, floor plans, renders, completed photos) for a project — across emails he sent and Drive folders. He needs a comprehensive inventory so he can decide what to share with a prospect (Harsha & Ido) and how (WhatsApp vs email).

This is the **upstream discovery phase** of dossier compilation: you don't know what exists yet. The user wants a complete picture before deciding what to compile/share.

## Workflow

### Phase 0: Resolve All Google Accounts

Do not assume which account holds the data. Call `gws_resolve_account` with no args to list ALL known accounts and their auth status:

```
gws_resolve_account  # no args → lists every service + token status
```

Typical accounts for NDR:
- `google-draas` (ndr@draas.com) — primary work account
- `google-ahfl` (ndr@ahfl.in) — secondary work
- `google-gmail` (nishantranka@gmail.com) — personal

### Phase 1: Gmail Search — Across Every Account

Search each account that has a token. Use broad query with date filter (last 6 months):

```python
query = 'Iris after:2026-02-28'
results = service.users().messages().list(userId='me', q=query, maxResults=50).execute()
```

**Variations to try:**
- Raw project name: `Iris`
- With attachment filter: `Iris has:attachment`
- From a specific person: `from:bharat Iris`
- Specific document types: `(brochure OR "floor plan" OR "floor plan") Iris`
- The `maxResults` default is 100 per page; use pagination (`pageToken`) for more.

### Phase 2: Extract Attachment Lists from Key Emails

For each relevant email, get full format + extract attachments:

```python
msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

def find_attachments(part, attach_list):
    if part.get('filename') and part['filename']:
        attach_list.append({
            'filename': part['filename'],
            'mimeType': part.get('mimeType',''),
            'size': part.get('body',{}).get('size',0),
            'attachmentId': part.get('body',{}).get('attachmentId','')
        })
    if 'parts' in part:
        for p in part['parts']:
            find_attachments(p, attach_list)

attachments = []
find_attachments(msg['payload'], attachments)
```

Also extract the **email body** (text/plain) — it often describes what was attached and why:

```python
def get_body_text(payload):
    if 'parts' in payload:
        for p in payload['parts']:
            if p['mimeType'] == 'text/plain':
                data = p['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            if 'parts' in p:  # nested
                for sub in p['parts']:
                    if sub['mimeType'] == 'text/plain':
                        data = sub['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    return ''
```

### Phase 3: Drive Search — Files + Folders

**Broad search by project name + file type:**

```python
# All Iris files of relevant types
q = "name contains 'Iris' and (mimeType contains 'pdf' or mimeType contains 'jpeg' or mimeType contains 'jpg' or mimeType contains 'png' or mimeType contains 'tiff')"

# Brochure/floorplan/images specifically
q2 = "(name contains 'Ranka' and name contains 'Iris') and (name contains 'brochure' or name contains 'floor' or name contains 'plan' or name contains 'photo' or name contains 'image' or name contains 'render' or name contains 'presentation')"

# Find project folders
q3 = "name contains 'Iris' and mimeType = 'application/vnd.google-apps.folder'"
```

**Recursive folder exploration:** Once you find folders, list their contents and recurse into subfolders:

```python
def list_children(folder_id, indent=0):
    q = "'{}' in parents".format(folder_id)
    results = service.files().list(q=q, fields='files(id,name,mimeType,size)', pageSize=50).execute()
    items = results.get('files', [])
    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            list_children(item['id'], indent + 1)
        else:
            print(f"{'  ' * indent}{item['name']} ({item.get('size','?')} bytes)")
```

### Phase 4: Cross-Reference Email ↔ Drive

When the user says "Bharat shared materials with me" — check:
1. Emails FROM Bharat (sales1.blr@draas.com) containing the project name
2. Emails the user SENT TO others with project attachments
3. Drive folders the user or Bharat created

The email body often lists the exact files sent (e.g., 13 attachments listed by name in the body text). Cross-reference these names with Drive items to identify duplicates and locate the originals.

### Phase 5: Present Organized Inventory

Group materials by category for the user's decision:

```
**Images** (9 files — exterior render, flat interiors, common area, gym, balcony)
**Floor Plans** (6 PDFs — all-apartment plans, even/odd floor, ground floor)
**Brochures/Presentations** (2 PDFs — 29 MB presentation, brochure)
**Legal Documents** (OC docs, sanctions, tax receipts — in Drive folders)
```

For each category, note:
- What was already sent to someone (and when/to whom)
- Where the originals live (email attachment vs Drive)
- File sizes (important for WhatsApp — large files need compression)

### Phase 6: User Decision Point

Present the inventory and wait. Do NOT compile or share anything until the user explicitly says what to share and how. Typical questions they'll answer:

- "Which of these do you want to share?"
- "WhatsApp link or email draft?"
- "All together or select items?"

## Pitfalls

- **Don't assume one account has everything** — NDR sends from ndr@draas.com, but Bharat sends to sales1.blr@draas.com and shared links from there. Always search all accounts.
- **`maxResults` default is 100** — use pagination (`pageToken`) for full coverage. For last-6-month searches, 50–100 is usually sufficient.
- **Email body is often HTML** — prefer `text/plain` parts. If none, decode `text/html` and strip tags with a simple regex or BeautifulSoup.
- **Drive search may miss items in shared/trashed folders** — the API by default excludes trashed. Explicitly add `and trashed = false` (it's the default but good practice).
- **File size for WhatsApp** — PDFs over ~10 MB may fail on WhatsApp. Flag large files and mention compression as an option.
- **Duplicate files across Drive folders** — the same floor plan PDF may appear in 3 different folders. Note duplicates; ask the user which to use.
- **RAR/DWG files** — these are CAD drawings and archives, not directly viewable. Flag them as "CAD drawings (DWG format)" so the user knows they exist but can't be casually shared.