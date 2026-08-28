# Gmail → Drive → New Draft Pipeline

Extract attachments from Gmail, rename per NDR convention, archive to Drive, then create a NEW draft (not a forward) to a different recipient with those Drive files attached.

Use this when the user says anything like:
- "Find the floor plans I sent to [person] in June, add the new combined plan, rename them all, file in Drive, and send to [new recipient]."
- "Take the attachments from these old emails, file them properly in Drive, and forward to [consultant]."

## When to use this instead of forwarding

A **forward** preserves the original email as context (From/Date/Subject block + commentary). A **new draft** is what you use when:
- The audience is different from the original recipients
- You want a fresh message body with the files as attachments only
- The original email body is irrelevant to the new recipient
- You need to combine files from MULTIPLE source emails into a single coherent message

## Full Pipeline

### Step 1 — Find the source emails

Use `build_service('gmail', 'v1', service_name=...)` to search. Run multiple queries — the user may have sent similar emails to different addresses on the same day:

```python
service = build_service('gmail', 'v1', service_name='google-draas')

queries = [
    'to:msingh@ircaindia.com after:2026/06/05 before:2026/06/07',
    'to:msingh@redsoul.co.in after:2026/06/05 before:2026/06/07',
]

seen_ids = set()
for q in queries:
    results = service.users().messages().list(userId='me', q=q, maxResults=5).execute()
    for m in results.get('messages', []):
        if m['id'] not in seen_ids:
            seen_ids.add(m['id'])
            # Fetch metadata
            msg = service.users().messages().get(userId='me', id=m['id'], format='metadata',
                metadataHeaders=['From','Subject','Date','To','Cc']).execute()
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            # Print or log for user to confirm which emails to use
```

**Key tip:** The user said "one email" but may have actually sent the same attachments in MULTIPLE emails (different recipients, same attachments). Always search all variants and list them before downloading.

### Step 2 — List attachments in each email

Walk the payload recursively to find all file attachments:

```python
def list_attachments(part, depth=0):
    prefix = '  ' * depth
    fname = part.get('filename', '')
    mime = part.get('mimeType', '')
    size = part.get('body', {}).get('size', 0)
    if fname:
        print(f"{prefix}FILE: {fname} ({mime}, {size} bytes)")
    for sub in part.get('parts', []):
        list_attachments(sub, depth + 1)

msg_full = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
list_attachments(msg_full['payload'])
```

### Step 3 — Download ALL attachments to a local temp dir

```python
output_dir = '/opt/data/floor_plans'  # or /opt/data/<project>_docs/
os.makedirs(output_dir, exist_ok=True)

def download_all_attachments(msg_id, output_dir):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    downloaded = []
    
    def walk_and_download(part):
        fname = part.get('filename', '')
        if fname and part.get('body', {}).get('attachmentId'):
            att_id = part['body']['attachmentId']
            att = service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=att_id
            ).execute()
            data = base64.urlsafe_b64decode(att['data'])
            path = os.path.join(output_dir, fname)
            with open(path, 'wb') as f:
                f.write(data)
            downloaded.append(path)
        for sub in part.get('parts', []):
            walk_and_download(sub)
    
    walk_and_download(msg['payload'])
    return downloaded
```

**Pitfall — duplicate downloads:** If the same attachment was sent in multiple emails (e.g. same JPG to different recipients), the download loop creates duplicate files with identical names in the same directory. The second write silently overwrites the first — which is usually fine (same content). But verify by checking file sizes after download.

**Pitfall — Gmail attachment truncation (confirmed Aug 2026):** `attachments().get()` can return TRUNCATED base64 for large binaries — symptoms: a PDF that opens with `%PDF` but `pdftotext` fails; a docx zip with bad central directory. If that happens, look for the same file in Drive (contracts/agreements are often mirrored there) and download via `drive.files().get_media()` instead. Do NOT retry the Gmail download more than twice.

### Step 4 — Rename files per NDR naming convention

NDR's convention: `YYYYMMDD_Entity_Description` — underscores only, no spaces, no dashes (except hyphens within entity/project names), no "(DD-MM-YYYY)" date formats.

```python
# Map old filenames to new names
rename_map = {
    'Aspra_206_FloorPlan.jpg': '20260606_Aspra_206_FloorPlan.jpg',
    'Brilla_004_FloorPlan.jpg': '20260606_Brilla_004_FloorPlan.jpg',
    'Crissa_401_FloorPlan.jpg': '20260606_Crissa_401_FloorPlan.jpg',
    # etc.
}
```

If the user also provides a NEW file (e.g. combined floor plan dropped into /tmp or /opt/data/tmp/), find and include it:

```python
import shutil
tmp_dir = '/opt/data/tmp'
if os.path.exists(tmp_dir):
    for f in os.listdir(tmp_dir):
        if 'Combined' in f or 'Combo' in f:
            src = os.path.join(tmp_dir, f)
            # Copy to staging dir
            shutil.copy2(src, os.path.join(output_dir, f))
```

The user-said timestamp (e.g. "just added the combined floor plan") maps to today's date in `YYYYMMDD` format.

### Step 5 — Upload to Drive with renamed filenames

```python
drive = build_service('drive', 'v3', service_name='google-draas')

# Find target folder
target_folder_id = "1K6g5RteoljJUmsRNIhn7eawA0NqFoeKr"  # Century Regalia Documents

# Check for existing files with same name (skip duplicates)
query = f"name='{new_name}' and '{target_folder_id}' in parents and trashed=false"
existing = drive.files().list(q=query, fields='files(id,name,webViewLink)', pageSize=1).execute()
if existing.get('files'):
    # Already exists — skip upload, just note the link
    pass
else:
    media = MediaFileUpload(src_path, resumable=False)
    body = {'name': new_name, 'parents': [target_folder_id]}
    result = drive.files().create(body=body, media_body=media, fields='id,name,webViewLink,size').execute()
```

**For files already on Drive** (the combined floor plan the user dropped into temp): they just need to be renamed and/or moved to the correct folder:

```python
# Rename
drive.files().update(fileId=file_id, body={'name': new_name}).execute()
# Move
drive.files().update(fileId=file_id, addParents=target_folder_id, removeParents=prev_parents).execute()
```

### Step 6 — Delete any prior draft on the same subject (cleanup)

Before creating the new draft, delete any earlier version so the user sees only one:

```python
drafts_result = gmail.users().drafts().list(userId='me', maxResults=10).execute()
for d in drafts_result.get('drafts', []):
    draft = gmail.users().drafts().get(userId='me', id=d['id'], format='metadata').execute()
    h = {hdr['name']: hdr['value'] for hdr in draft['message']['payload']['headers']}
    if 'Individual Floor Plans' in h.get('Subject', ''):
        gmail.users().drafts().delete(userId='me', id=d['id']).execute()
        print(f"Deleted old draft: {d['id']}")
```

### Step 7 — Create new draft with Drive files as attachments

Since `gws_skill_bridge.draft_create()` does NOT support file attachments, use the raw Gmail API with `MIMEMultipart("mixed")`:

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Download files from Drive to a temp directory for MIME building
tmpdir = '/opt/data/email_attachments'
os.makedirs(tmpdir, exist_ok=True)

# Build MIME
msg = MIMEMultipart("mixed")
msg["To"] = "ankush@infimaxadvisors.com, amusaddi@hotmail.com"
msg["Subject"] = "Century Regalia — Individual Floor Plans & Crissa 401+404 Combined Unit"

# Plain text body
body_text = """Hi Ankush,

Please find attached the individual floor plans for the available units at Century Regalia, along with a combined floor plan for Crissa 401 & 404.

Key Highlights:
1. Crissa 401 + 404 Combined Unit — combined floor plan attached
2. Individual floor plans attached for each unit

Best regards,
Nishant Ranka"""
msg.attach(MIMEText(body_text.strip(), "plain"))

# Attach each Drive file
for file_info in files_to_attach:  # [(fname, drive_file_id), ...]
    fname, file_id = file_info
    req = drive.files().get_media(fileId=file_id)
    local_path = os.path.join(tmpdir, fname)
    with open(local_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, req)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    
    with open(local_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{fname}"')
        msg.attach(part)

# Create the draft
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
draft = gmail.users().drafts().create(
    userId="me",
    body={"message": {"raw": raw}}
).execute()

print(f"Draft created: {draft['id']}")
print(f"Gmail link: https://mail.google.com/mail/u/0/#drafts?compose={draft['message']['id']}")
```

### Step 8 — Verify

```python
# Verify the draft exists and has the right number of attachments
verify = gmail.users().drafts().get(userId='me', id=draft['id'], format='full').execute()
h = {hdr['name']: hdr['value'] for hdr in verify['message']['payload']['headers']}
print(f"Subject: {h.get('Subject')}")
print(f"To: {h.get('To')}")
print(f"CC: {h.get('Cc', '(none)')}")

# Count attachments
att_count = 0
def count_parts(part):
    global att_count
    if part.get('filename'):
        att_count += 1
    for p in part.get('parts', []):
        count_parts(p)
count_parts(verify['message']['payload'])
print(f"Attachments: {att_count}")
```

## Key differences from the Drive-to-Draft pipeline

| Aspect | Drive-to-Draft | Gmail-to-Drive-to-Draft |
|--------|---------------|------------------------|
| File source | Drive search only | Gmail attachments first → Drive archival |
| Renaming | Files may already be named correctly | Almost always needs renaming per NDR convention |
| Recipient | Original recipient or same-thread | NEW recipient (different person) |
| Threading | `threadId` from existing thread | No threading — brand new message |
| Body content | Reply/forward context | Fresh message introducing the attachments |
| Number of source emails | Usually 1 thread | Multiple emails (same files to different people) |

## Pitfalls

- **Wrong mailbox identity (confirmed Aug 2026):** Terminal subprocesses can resolve to psingh@draas.com instead of ndr@draas.com. ALWAYS verify: `profile = gmail.users().getProfile(userId='me').execute(); print(f"Authenticated as: {profile['emailAddress']}")` before downloading anything. Fix: prefix shell command with `HERMES_SESSION_USER_ID=ndr`.
- **Draft resource ID vs message ID:** When deleting prior drafts, use `drafts().list()` to get the draft resource ID (not `messages().list(q='in:drafts')` which returns message IDs). Draft resource ID goes to `drafts().delete()`.
- **Gmail attachment API can truncate:** For large binary files, fall back to Drive download. See Step 3 pitfall.
- **BCC not supported by gws_skill_bridge:** If the user wants someone BCC'd, use raw `EmailMessage` from `email.message` module — set Bcc header before encoding. Verify with `drafts().get()` that `DRAFT` label is present (Gmail strips Bcc from API responses for security).
- **MIME changes the effective size:** Base64 encoding inflates file size by ~33%. The Gmail cap is 35 MB on the `raw` field. Print `len(raw)` / 1048576 before creating the draft — if > 35 MB, compress PDFs first with `gs` (see main email-drafter skill's attachment compression recipe).
