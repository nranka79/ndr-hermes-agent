# Gmail Attachment → Drive Upload Pipeline

When a user asks you to find an invoice/bill/document in their email and upload it to Drive with proper naming.

## Workflow

### 1. Search Gmail for the email

Use Gmail search query syntax. The user often provides partial sender name and document type:

```python
# Broad search first, then narrow
query = "from:arvind Ranka Amber invoice OR bill OR revised"
results = gmail.users().messages().list(userId="me", q=query, maxResults=20).execute()
```

For each result, fetch with `format="metadata"` and `metadataHeaders=["From","To","Subject","Date"]`:

```python
msg = gmail.users().messages().get(
    userId="me", id=m["id"],
    format="metadata",
    metadataHeaders=["From","To","Cc","Subject","Date"]
).execute()
headers = {h["name"]: h["value"] for h in msg.get("payload",{}).get("headers",[])}
```

Present a summary to the user — date, subject, sender — so they can confirm which email.

### 2. Download the attachment

Fetch the full message and walk parts for attachments:

```python
msg = gmail.users().messages().get(userId="me", id=m["id"], format="full").execute()
parts = [msg["payload"]]
while parts:
    part = parts.pop(0)
    if "parts" in part:
        parts.extend(part["parts"])
    filename = part.get("filename", "")
    if filename and part.get("body", {}).get("attachmentId"):
        att_id = part["body"]["attachmentId"]
        att = gmail.users().messages().attachments().get(
            userId="me", messageId=m["id"], id=att_id
        ).execute()
        file_bytes = base64.urlsafe_b64decode(att["data"])
        local_path = f"/tmp/{filename}"
        with open(local_path, "wb") as f:
            f.write(file_bytes)
```

### 3. Identify the document

For PDFs, extract text with fitz/pymupdf to confirm the document type, date, amount, parties:

```python
import fitz
doc = fitz.open(local_path)
text = ""
for page in doc:
    text += page.get_text()
doc.close()
# Look for: invoice number, date, amount, sender name, description
```

Present key findings to the user (invoice number, date, amount) for confirmation.

### 4. Rename per convention

DRAAS naming: `YYYYMMDD_ProjectName_Entity_DocumentType_DocNumber.pdf`

The date should match the **document/invoice date** (not the email date) when the document has its own date. If not, use email date.

```python
drive_name = "20260502_RankaAmber_AJArchitects_RevisedInvoice_AJA-26-27-001.pdf"
```

### 5. Upload to Drive

```python
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload(local_path, mimetype="application/pdf", resumable=True)
body = {"name": drive_name}
uploaded = drive.files().create(
    body=body, media_body=media,
    fields="id, name, webViewLink"
).execute()
```

Upload to My Drive root (omit `parents`). If the user wants it in a specific folder, note the 403 limitation for shared folders and offer the link at root level instead.

### 6. Present the result

```
Uploaded to Drive:
📄 {drive_name}
🔗 {webViewLink}
```

Include a comparison table if the user wants to compare original vs revised (amounts, dates, invoice numbers).

## Common email senders for DRAAS invoices

| Sender | Email | Documents |
|---|---|---|
| Arvind Jain (AJ Architects) | arch_arvind2000@yahoo.co.in | Amber architectural invoices |
| Bhavik Ranka | bhavik@draas.com | Project management, NOCs |
| Eshwari Chamundeshwari | echamundeshwari@draas.com | OC, property tax, certificates |
| Piyush Ranka | piyush@draas.com | Legal, registration |
