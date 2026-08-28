# Email Reply — Resume Attachment Decision Tree

## Situation
User asks to reply to an email chain (Reply All) and attach a resume. Two sub-cases:
1. Resume was shared as an **attachment** in the chain
2. Resume was shared as a **drive link** in the chain
3. Neither found → fallback to Drive search → present to user for confirmation

---

## Step-by-Step

### Phase 1 — Identify the target email
1. Find the last email SENT to the recipient (not received)
2. Use: `gmail.users().messages().list(q='to:recipient@domain subject:Subject', maxResults=5)`
3. Get the message ID of the last outbound email in the thread

### Phase 2 — Check for attachments in the chain
Get all messages in the thread (both sent and received, going back as far as needed):
```python
email_ids = ['<msg_id_1>', '<msg_id_2>', ...]  # from search results

for eid in email_ids:
    msg = gmail.users().messages().get(userId='me', id=eid, format='full').execute()
    def collect_attachments(parts):
        for p in parts:
            fn = p.get('filename','')
            at_id = p.get('body',{}).get('attachmentId','')
            if fn and at_id:
                print(f'  {fn} | {p["mimeType"]} | {at_id}')
            if 'parts' in p:
                collect_attachments(p['parts'])
    if 'parts' in msg['payload']:
        collect_attachments(msg['payload']['parts'])
```

### Phase 3 — Check for drive links in the body
```python
import re, base64

def get_text(payload):
    texts = []
    for p in payload.get('parts', []):
        if p['mimeType'] in ['text/plain', 'text/html']:
            data = p['body'].get('data','')
            if data:
                try:
                    texts.append(base64.urlsafe_b64decode(data).decode('utf-8', errors='replace'))
                except: pass
        if 'parts' in p:
            texts.extend(get_text(p))
    return texts

texts = get_text(msg['payload'])
full_text = '\n'.join(texts)
drive_links = re.findall(r'https://drive\.google\.com[^\s<>"\']+', full_text)
```

### Phase 4 — Fallback: search Drive for resume
```python
drive = build_service('drive', 'v3')
results = drive.files().list(
    q='name contains "resume" or name contains "Resume" or name contains "CV"',
    fields='files(id, name, mimeType)',
    pageSize=20
).execute()
# Find one matching the user's name (e.g. "Nishant Ranka - Professional Resume.pdf")
```

### Phase 5 — Present options to user
If no attachment and no drive link found in chain:
1. Say "No resume found in the email chain"
2. If Drive search found candidate(s): show them as images/PDF preview
3. Ask user to confirm which resume to use

### Phase 6 — Draft the Reply All
When user confirms the resume and new recipient TO address:
1. Get the last sent email's thread ID
2. Use `gmail.users().messages().send()` with `threadId` to reply in same thread
3. TO = new address, CC = original recipient(s) from the last sent email
4. Attach the confirmed resume file

---

## World of Visa — Confirmed Findings (2026-06-02)

**Email chain scanned:** Anbu (anand@worldvisa.in), QC (qc@worldvisa.in), Kavitha (kavitharamaraj@worldvisa.in)

**Last outbound email:** 30 May 2026, `to: anand@worldvisa.in`, subject "Re: Sample Reference Letter and Guidelines (Systems Analysts)"

**Attachments found in chain:** Only reference letters and info sheets — NO resume, NO CV

**Drive links found in chain:** None

**Drive resume found:** `Nishant Ranka - Professional Resume.pdf` (ID: `1HKFwizPuDpBnBz_5t708qJpa-_nxfLIQ`) — 2 pages, confirmed existing

**User guidance:** TO goes to qc@worldvisa.in, CC goes to anand@worldvisa.in

---

## Resume Download + Preview Pattern

```python
from googleapiclient.http import MediaIoBaseDownload
import io, subprocess

# Download
req = drive.files().get_media(fileId='<file_id>')
fh = io.FileIO('/tmp/resume.pdf', 'wb')
MediaIoBaseDownload(fh, req).next_chunk()

# Convert to images for Telegram preview
subprocess.run(['pdftoppm', '-r', '150', '-png', '/tmp/resume.pdf', '/tmp/resume_page'])
# Send pages as MEDIA:/tmp/resume_page-1.png, MEDIA:/tmp/resume_page-2.png, etc.
```

---

## Key Lesson

User said: *"I want you to pull out the resume from the email chain I have shared with World of Visas. If there is no resume in the email chain I have shared with World of Visas, then I would like to review this resume you found on my drive"*

→ The fallback to Drive was NOT automatic in this session. User had to prompt for it. In future sessions, if no attachment and no drive link found in Phase 2+3, volunteer the Drive search automatically and present the Drive resume for review — don't wait to be asked.