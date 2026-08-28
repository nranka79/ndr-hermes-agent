# Email Chain Analysis — Service Provider Communication Summary

## What This Is

When a user asks to analyze a long email chain with a service provider (visa consultant, immigration agent, legal firm, etc.) and produce a briefing document for a new handler, this skill governs the workflow: email extraction, content analysis, HTML summary generation, numbered attachment extraction, and Drive upload.

**Trigger phrases:**
- "analyze all emails from [service provider]"
- "summarize everything that has happened between me and [company]"
- "make a detailed summary for the new person joining [company]"
- "compile all communication from [consultant]"
- "extract all documents from the email chain and number them"

---

## Workflow

### PHASE 1 — Email Extraction

1. Use `gws_auth.build_service('gmail', 'v1')` with per-user token
2. Search for emails with the service provider domain(s):
   ```python
   queries = ['from:worldvisa.in', 'to:worldvisa.in', 
              'from:kavitharamaraj@worldvisa.in', 'subject:visa OR subject:PR OR subject:GTI']
   ```
3. Fetch ALL matching messages with `format=full` — extract: subject, from, to, date, threadId, snippet, body, html_body, attachments
4. Save to `/tmp/emails_full.json` for processing

**Email body extraction pattern:**
```python
def get_body(payload):
    body_text, html_text = '', ''
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body_text += base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                if data:
                    html_text += base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            elif 'parts' in part:
                b, h = get_body(part)
                body_text += b
                html_text += h
    return body_text, html_text
```

**Attachment extraction pattern:**
```python
def find_attachments(payload):
    atts = []
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('filename'):
                atts.append({
                    'filename': part['filename'],
                    'mimeType': part.get('mimeType', ''),
                    'size': part.get('body', {}).get('size', 0),
                    'attachmentId': part['body'].get('attachmentId', '')
                })
            if 'parts' in part:
                atts.extend(find_attachments(part))
    return atts
```

### PHASE 2 — HTML Summary Generation via delegate_task

Use `delegate_task` with `role=leaf` to generate the HTML document. Pass:
- The email data JSON
- The attachment list JSON
- The goal: create a comprehensive HTML at `/tmp/email_chain_summary.html`

**HTML document structure should include:**
1. **Title/Cover** — case name, client name, service provider, date range
2. **Executive Summary** — key facts about the relationship
3. **Chronological Email Chain** — each email with date, from→to, subject, content summary, attachments
4. **Document Index Table** — all numbered attachments (DOC_XXX format)
5. **Key Decisions/Agreements** — important outcomes
6. **Current Status & Next Steps** — pending items

**delegate_task approach:**
```python
delegate_task(
    goal="Create HTML summary from email data. Data in /tmp/emails_full.json and /tmp/attachments_list.json. Write to /tmp/email_chain_summary.html. Include: executive summary, chronological email chain, document index table with DOC_XXX numbering, key decisions, current status.",
    role="leaf",
    tasks=[{"goal": "...", "toolsets": ["terminal", "file"]}]
)
```

### PHASE 3 — Attachment Download & Numbering

1. Create `/tmp/attachments/` directory
2. For each attachment with a valid `attachmentId`:
   - Download via `gmail.users().messages().attachments().get()`
   - Save with `DOC_<NNN>_<original_filename>` naming
   - Track: doc_number, original_filename, email_date, email_subject, file_size
3. Save attachment list to `/tmp/attachment_list.json`

**CRITICAL — skip .ics calendar files:** They are not documents, just meeting invites.

### PHASE 4 — Drive Upload

1. Find or create the target folder:
   - Search for folder under user's personal folder
   - Create new folder named after the service provider (e.g., "World of Visa")
   - Place under user's **Personal** folder (ID: `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE`)

2. Upload the HTML summary first

3. Upload all numbered documents:
   ```python
   from googleapiclient.http import MediaFileUpload
   metadata = {'name': filename, 'parents': [folder_id], 'mimeType': mime}
   media = MediaFileUpload(file_path, mimetype=mime)
   drive_service.files().create(body=metadata, media_body=media, fields='id, name, webViewLink')
   ```

4. Determine mime type by extension:
   - `.pdf` → `application/pdf`
   - `.docx` → `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
   - `.xlsx` → `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
   - `.zip` → `application/zip`
   - default → `application/octet-stream`

---

## Drive Folder Structure

```
Personal/ (0B1Oc8cSaJXPGYkQtYXJDQWVBUVE)
└── [Service Provider Name]/
    ├── email_chain_summary.html
    ├── DOC_001_original_name.pdf
    ├── DOC_002_original_name.docx
    └── ...
```

---

## Key Patterns

| Task | Pattern |
|------|---------|
| Find user's personal folder | `'0B1Oc8cSaJXPGYkQtYXJDQWVBUVE' in parents` query |
| Create folder under personal | `parents: [personal_folder_id]`, mimeType: folder |
| Number attachments | `DOC_<NNN>_<original_filename>` — zero-padded 3 digits |
| HTML summary structure | cover → executive summary → email chain → doc index → decisions → next steps |
| Attachment download | `users().messages().attachments().get()` — NOT the message itself |
| Skip calendar .ics files | They are meeting invites, not documents |

---

## Pitfalls

1. **OAuth token for Gmail vs Drive** — Both use `gws_auth` but `build_service('gmail', 'v1')` vs `build_service('drive', 'v3')`. Don't mix them.

2. **attachmentId vs messageId** — Attachments are downloaded using `messages().attachments().get()` with the attachment ID, not the message ID.

3. **Drive file creation with media** — Use `MediaFileUpload` object, not raw bytes. The `media_body` parameter expects a `MediaUpload` subclass instance, not `io.BytesIO`.

4. **Finding personal folder** — The ID `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE` is the user's personal folder on this account. Use it as the parent when creating service-provider subfolders.

5. **delegate_task with leaf role** — For HTML generation (complex output creation), use `role=leaf` so the sub-agent executes directly rather than trying to coordinate further delegation.