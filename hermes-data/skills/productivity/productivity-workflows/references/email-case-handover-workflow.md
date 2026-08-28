# Email Case Handover Document Workflow

Create a flat, email-safe HTML document summarizing email chains (e.g., for handing over a case to a new consultant). Used when a new person needs to understand everything that transpired in a communication thread.

**Use when:** User says "summarize all emails from X", "create a handover document", "analyze this email chain and make a briefing note", "compile everything from this thread into one document for the new person".

---

## Workflow

### PHASE 1 — Fetch Emails from Gmail

Use `tools.gws_auth.build_service('gmail', 'v1')` — NOT gws_sa. Personal email access requires per-user OAuth.

```python
from tools.gws_auth import build_service
service = build_service('gmail', 'v1')

# Search for relevant emails
results = service.users().messages().list(
    userId='me',
    q='from:worldvisa.in OR to:worldvisa.in',
    maxResults=500
).execute()

messages = results.get('messages', [])

# Fetch full details for each message
for msg in messages:
    msg_detail = service.users().messages().get(
        userId='me',
        id=msg['id'],
        format='full'
    ).execute()
```

### PHASE 2 — Download Attachments with DOC Numbering

```python
from googleapiclient.http import MediaFileUpload
import base64, os

doc_counter = 1
for email in emails:
    for att in email['attachments']:
        if att['filename'].endswith('.ics'):
            continue  # Skip calendar invites
        
        result = service.users().messages().attachments().get(
            userId='me',
            messageId=email['id'],
            id=att['attachmentId']
        ).execute()
        
        file_data = base64.urlsafe_b64decode(result['data'])
        numbered_filename = f"DOC_{doc_counter:03d}_{att['filename']}"
        
        file_path = f'/tmp/attachments/{numbered_filename}'
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        doc_counter += 1
```

### PHASE 3 — Identify User-Submitted vs Sample Documents

**User-submitted = outgoing emails with attachments** (Nishant/Roshini to WorldVisa):
```python
outgoing_addresses = ['ndr@draas.com', 'ndr@drahomes.in', 'rnr@draas.com', 'rmurjani@gmail.com']
is_outgoing = any(addr in email['from'] for addr in outgoing_addresses)
```

**Sample documents = incoming from WorldVisa** — these are templates/guides, not user paperwork.

### PHASE 4 — Create Email-Safe Flat HTML

**Critical: User said "copy-paste into email" — NO collapsible elements, NO complex CSS.**

```html
body { font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; margin: 40px; max-width: 1000px; }
h1 { color: #1a1a6e; font-size: 24px; border-bottom: 3px solid #1a1a6e; }
table { border-collapse: collapse; width: 100%; margin: 15px 0; }
th { background-color: #1a1a6e; color: white; }
```

**Required sections:**
1. **Executive Briefing Note** — narrative summary of entire case, current status, next steps
2. **Documents to Attach** — highlighted table of DOC_XXX numbers for files to attach to the email
3. **Email Summary Table** — Date | From | To | Type (IN/OUT) | Subject | Summary | Attachments
4. **Submitted Documents Detail** — DOC_XXX | Filename | Description | Date | Status

**Email-safe rules:**
- No JavaScript, no CSS classes that require external files
- All CSS inline or in `<style>` block in `<head>`
- No collapsible sections (`<details>`/`<summary>`)
- Plain HTML tables for data — no advanced UI components
- `max-width: 1000px` to prevent formatting issues on email clients

### PHASE 5 — Upload to Google Drive

```python
drive_service = build_service('drive', 'v3')

# Create folder under Personal (ID: 0B1Oc8cSaJXPGYkQtYXJDQWVBUVE)
folder_metadata = {
    'name': 'World of Visa',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': ['0B1Oc8cSaJXPGYkQtYXJDQWVBUVE']
}
folder = drive_service.files().create(body=folder_metadata, fields='id').execute()

# Upload HTML
metadata = {'name': 'Summary.html', 'parents': [folder['id']], 'mimeType': 'text/html'}
media = MediaFileUpload('/tmp/summary.html', mimetype='text/html')
result = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
```

---

## Critical Distinctions

### Documents User Submitted (attach to email)
These are the actual paperwork: reference letters, employment forms, salary documents. They have DOC_XXX numbers and are what the new contact needs to see.

### Sample Documents from Company (ignore for email)
When a company sends sample templates (e.g., "Sample Reference Letter" from WorldVisa), these are for reference only — do not attach to handover email.

### Classification Logic
```python
if is_outgoing:
    # User submitted this — HIGHLIGHT in table
    submitted_docs.append(att)
else:
    # Sample/template from company — IGNORE for handover
    pass
```

---

## Common Case Types This Workflow Handles

1. **PR/Migration case handover** (WorldVisa scenario) — compile all email docs for new agent
2. **Legal case status update** — summarize correspondence for new lawyer
3. **Project handover** — vendor/consultant transition documentation
4. **Real estate transaction summary** — compile all emails + docs for buyer/new agent

---

## Pitfalls

1. **Use `gws_auth.build_service('gmail', 'v1')` NOT `gws_sa`** — SA tokens are for shared business data, not personal Gmail. Using SA for Gmail raises `ValueError`.

2. **Calendar invites (.ics) — skip these** — they clutter the document list and have no useful attachment content.

3. **Check duplicate attachments** — same file may be sent multiple times (e.g., DRA Reference Letter v2, v2 (1), v2 (2)). Group by latest version only.

4. **DOC numbering** — assign numbers sequentially in order of extraction. User refers to documents as "DOC_001", "DOC_002" — this is how they track what to re-attach in emails.

5. **Email body content** — do NOT reproduce full email body in the summary table. Just a 1-2 line summary. Full content is in the email itself if they need it.

6. **Personal folder ID** — for Drive uploads under "Personal" folder, the ID is `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE`. Do NOT hardcode folder names — always query first.

7. **Flat HTML for email** — The user explicitly said "I intend to copy paste the content into an email." Never use collapsible sections, complex JavaScript, or CSS that won't render in email clients. Keep it simple.