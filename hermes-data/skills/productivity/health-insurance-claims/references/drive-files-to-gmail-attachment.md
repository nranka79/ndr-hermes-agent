# Drive Files → Gmail Draft Attachments

**Validated:** 16 July 2026 — 24 PDFs (19MB) successfully attached to a claim reimbursement draft sent to Medi Assist TPA.

## Why Not `gws_skill_bridge.draft_create`

The bridge does not accept attachments. Use the raw Gmail API directly.

## Full Working Pattern

### 1. Download files from Drive

```python
from tools.gws_auth import build_service
import os

drive = build_service("drive", "v3", service_name="google-draas")

files_to_attach = {
    "FILE_ID_1": "01_Category_Description.pdf",
    "FILE_ID_2": "02_Category_Description.pdf",
    # ...
}

local_dir = "/opt/data/claim_temp/"
os.makedirs(local_dir, exist_ok=True)

for fid, fname in files_to_attach.items():
    content = drive.files().get_media(fileId=fid).execute()
    with open(os.path.join(local_dir, fname), "wb") as f:
        f.write(content)
```

### 2. Build MIME multipart/mixed message

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email.encoders
import base64

msg = MIMEMultipart("mixed")
msg["To"] = "recipient@example.com"
msg["Cc"] = "cc@example.com"
msg["From"] = "Sender Name <sender@email.com>"
msg["Subject"] = "Your Subject"

# Body (plain text)
body = """Full email body text here..."""
text_part = MIMEText(body, "plain", "utf-8")
msg.attach(text_part)

# Attachments
for fname in sorted(os.listdir(local_dir)):
    filepath = os.path.join(local_dir, fname)
    with open(filepath, "rb") as f:
        att = MIMEBase("application", "pdf")
        att.set_payload(f.read())
        email.encoders.encode_base64(att)
        att.add_header("Content-Disposition", "attachment", filename=fname)
        msg.attach(att)
```

### 3. Create draft (delete old first)

```python
gmail = build_service("gmail", "v1", service_name="google-draas")

# Delete old draft with same subject
drafts = gmail.users().drafts().list(userId="me").execute()
for d in drafts.get("drafts", []):
    draft_data = gmail.users().drafts().get(userId="me", id=d["id"], format="minimal").execute()
    for h in draft_data["message"]["payload"]["headers"]:
        if h["name"] == "Subject" and "POLICY_NUMBER" in h["value"]:
            gmail.users().drafts().delete(userId="me", id=d["id"]).execute()
            break

# Create new draft with attachments
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
new_draft = gmail.users().drafts().create(
    userId="me",
    body={"message": {"raw": raw}}
).execute()

draft_id = new_draft.get("id")
```

### 4. Verify the draft

```python
draft_check = gmail.users().drafts().get(userId="me", id=draft_id, format="full").execute()
# Count attachment parts
parts = [draft_check["message"]["payload"]]
att_count = 0
while parts:
    p = parts.pop(0)
    if "filename" in p and p["filename"] and p.get("mimeType") != "text/plain":
        att_count += 1
    if "parts" in p:
        parts.extend(p["parts"])
print(f"{att_count} attachments in draft {draft_id}")
```

## Key Gotchas

- **MIMEMultipart('mixed')** is essential — `'alternative'` won't carry attachments
- **File IDs from Drive are NOT guessable from filenames** — always fetch via `drive.files().list(q="name contains 'xxx'")` first
- **Large attachment bundles** (~19MB total) work fine — Gmail's attachment limit is 25MB per message
- **base64.urlsafe_b64encode** (not standard base64) — the Gmail API expects URL-safe encoding
- **Old draft matching** — match by policy number in subject, not exact subject text (drafts may have minor differences)
- **Cleanup** — temp directory (`/opt/data/claim_temp/`) can be deleted after verification
