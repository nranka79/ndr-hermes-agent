# Email Attachment → Drive Upload Pipeline

Common recurring pattern: find a specific email by sender + subject, download its attachment(s), analyze/OCR the content, rename per convention, upload to Drive, return link.

## Full Pipeline

### Step 1: Search Gmail for the target email

```python
# Search by sender + subject keywords
query = "from:arch_arvind2000@yahoo.co.in Ranka Amber floor plan OR layout OR option"
results = service.users().messages().list(userId="me", q=query, maxResults=10).execute()

# Get full details of each match
for m in results.get("messages", []):
    msg = service.users().messages().get(userId="me", id=m["id"], format="metadata",
        metadataHeaders=["From", "To", "Cc", "Subject", "Date"]).execute()
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    print(headers.get("Date",""), "|", headers.get("Subject",""))
```

### Step 2: Download attachments

```python
import base64

# Get full message with payload
msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()

# Walk the payload tree looking for attachments
parts = [msg["payload"]]
while parts:
    part = parts.pop(0)
    if "parts" in part:
        parts.extend(part["parts"])
    filename = part.get("filename", "")
    if filename and part.get("body", {}).get("attachmentId"):
        att_id = part["body"]["attachmentId"]
        mime = part.get("mimeType", "")
        att = service.users().messages().attachments().get(
            userId="me", messageId=msg_id, id=att_id).execute()
        data = att.get("data", "")
        file_bytes = base64.urlsafe_b64decode(data)
        
        local_path = f"/tmp/{filename}"
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        print(f"Saved: {local_path} ({len(file_bytes)/1024:.1f} KB)")
```

### Step 3: Analyze the attachment (PDF)

For architectural plans, invoices, and documents:

```python
import fitz
doc = fitz.open(local_path)
print(f"Pages: {len(doc)}")
text = ""
for page in doc:
    text += page.get_text()
doc.close()

# Look for key data:
# - Option/plan labels: "OPT 1", "OPT 2", "GROUND FLOOR PLAN", etc.
# - Area values: "AREA - 161.16 SQ.M"
# - Table headers: "FAR", "BUILT UP", "SETBACK", etc.
# - Corridor dimensions, room counts, unit layouts
```

For scanned or image-based PDFs (fitz returns empty), fallback to:
```bash
# Convert to images for vision analysis
pdftoppm -png -r 150 input.pdf /tmp/page_prefix
# Then analyze each page image
```

### Step 4: Name per convention & upload to Drive

Use the DRAAS naming convention: `YYYYMMDD_ProjectName_DocumentType_[Version].pdf`

- Date = document content date OR email date, whichever is more relevant
- Project name (e.g., "RankaAmber", "RankaIris")
- Document type (e.g., "RevisedInvoice", "FloorPlan_OPT1", "SanctionPlan")
- Optional version/ID (e.g., "AJA-26-27-001")

```python
from googleapiclient.http import MediaFileUpload

drive_name = f"{date_str}_{descriptive_name}.pdf"
media = MediaFileUpload(local_path, mimetype="application/pdf", resumable=True)

uploaded = drive.files().create(
    body={"name": drive_name},
    media_body=media,
    fields="id, name, webViewLink"
).execute()

print(f"Link: {uploaded['webViewLink']}")
```

### Step 5: Confirm with user

Present a summary:
- What email was found (date, subject, sender)
- What the attachment contains (key extracted data)
- Where it was uploaded (link)

Let the user confirm before sending in workflows that need user approval.

## Pitfalls

1. **Multiple emails with the same attachment** — The same PDF may be forwarded multiple times. Check email dates and pick the most recent.
2. **PDF text extraction limits** — `fitz.get_text()` works for programmatically-generated PDFs (invoices, text documents). Scanned/image PDFs need `pdftoppm` + OCR/vision.
3. **Per-user token** — Gmail and Drive operations use per-user OAuth via `gws_auth`. Do NOT use `gws_sa` for Gmail/Drive.
4. **Missing access_token field** — If token file uses `"token"` instead of `"access_token"`, rename before using. See `gws-auth-helper-bug-workaround.md`.

## Advanced: Full-Thread Attachment Filing (Multi-Account, Multiple Emails)

**Trigger:** A user asks to "file all attachments from that email thread to the project folder in Drive." The thread spans multiple emails, may cross multiple accounts, and the Drive target needs discovery.

### 1. Discover the thread

Search across relevant accounts. For Nishant, try DRAAS first (most legal/business correspondence lands here), then AHFL/Personal if needed:

```python
from tools.gws_auth import build_service

for label, svc_name in [("draas", None), ("ahfl", "google-ahfl"), ("gmail", "google-gmail")]:
    service = build_service("gmail", "v1", service_name=svc_name)
    results = service.users().messages().list(userId="me", q="case number OR sender keywords", maxResults=10).execute()
    # Inspect each result's date, subject, sender
```

### 2. Extract all attachments from all messages in the thread

Get the thread and walk every message's MIME tree:

```python
# Get the thread
thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()

# Reusable attachment finder
def find_attachments(part):
    """Recursively walk MIME parts, yield (filename, attachmentId) for real attachments."""
    fn = part.get("filename", "")
    if fn and part.get("body", {}).get("attachmentId"):
        yield fn, part["body"]["attachmentId"]
    if "parts" in part:
        for p in part["parts"]:
            yield from find_attachments(p)

# Collect all attachments across all messages in the thread
all_atts = {}
for msg in thread["messages"]:
    for fn, att_id in find_attachments(msg["payload"]):
        if fn != "image001.png":  # Skip inline sig logos
            # Download
            att = service.users().messages().attachments().get(
                userId="me", messageId=msg["id"], id=att_id).execute()
            data = base64.urlsafe_b64decode(att["data"])
            local_path = f"/tmp/cma742/{fn}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(data)
            all_atts[fn] = {"path": local_path, "size": len(data)}
```

### 3. Discover the correct Drive folder

Search the Drive hierarchy for the project folder and legal subfolder:

```python
# Find project folder by name (try multiple name variants)
for q in [
    "name contains 'Sevaganapalli' or name contains 'Saveganapalli'",
    "name contains 'Litigation'",
]:
    results = drive.files().list(q=q, spaces="drive", fields="files(id, name, mimeType, parents)", pageSize=20).execute()

# Navigate down: Project Folder > Legal_and_Title > Litigation > [Create Case Subfolder]
```

**DRAAS project folder convention:** `ProjectName > 01_Legal_and_Title_Docs > Litigation > [Case Name e.g. CMA 742 of 2026]`

If the case subfolder doesn't exist, create it:
```python
folder = drive.files().create(body={
    "name": "CMA 742 of 2026",
    "parents": [litigation_folder_id],
    "mimeType": "application/vnd.google-apps.folder"
}, fields="id, name").execute()
```

### 4. Rename with YYYYMMDD convention and upload

Nishant's preference: `YYYYMMDD_DescriptiveName.pdf`. Map each original filename to a descriptive rename:

```python
from googleapiclient.http import MediaFileUpload

rename_map = {
    "CMA 742 of 2026.pdf": "20260619_CMA742_CourtPapers_Served.pdf",
    "Engagement Letter.pdf": "20260604_CMA742_EngagementLetter_CMSIndusLaw.pdf",
    # ... etc
}

for orig_name, dest_name in rename_map.items():
    if orig_name in all_atts:
        media = MediaFileUpload(all_atts[orig_name]["path"], resumable=True)
        uploaded = drive.files().create(body={
            "name": dest_name,
            "parents": [case_folder_id],
            "description": f"From CMA No. 742 of 2026 email thread — originally: {orig_name}"
        }, media_body=media, fields="id, name, size").execute()
```

### 5. Present the result

```
**12 files filed under:** Project > Legal_Title > Litigation > CMA 742 of 2026
- `20260619_CMA742_CourtPapers_Served.pdf` (7.5 MB) — from Apsaraa
- `20260604_CMA742_EngagementLetter_CMSIndusLaw.pdf` (0.4 MB) — from Apsaraa
- `20260602_CMA742_SpeedPostNotice_Received.pdf` (1.7 MB) — from your sent email
...

🔗 https://drive.google.com/drive/folders/<folder_id>
```

### Pitfalls

- **image001.png / logo images** — Most Outlook-sent emails embed company logos as inline attachments. Skip these (check filename and size < 10 KB).
- **Attachment already on Drive but in a different folder** — The same PDF may already exist under a different path (e.g., "Legal Notice > OS 7-2025"). The user's ask is about the project-specific Litigation folder — upload there and let dedup happen later.
- **Nishant sent attachments from a different account** — The user's original briefing may be in ndr@draas.com (sent) while the law firm's reply is in ndr@drahomes.in (forwarded). Check both.
- **The `basement` issue with Gmail API attachments** — If `attachmentId` returns empty `data` with only `size`, the attachment is too large for the inline API. Use `users().messages().attachments().get()` with the attachmentId from the body, not the raw message fetch.
- **Clean up temp files** — Delete `/tmp/cma742/` (or whatever temp dir) after successful upload to avoid filling disk space.
