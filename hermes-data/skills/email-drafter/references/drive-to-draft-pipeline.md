# Drive → Gmail Draft Pipeline

Building a Gmail draft with documents sourced from Google Drive requires a multi-step pipeline that `draft_create` / `draft_reply_create` (gws_skill_bridge) cannot handle directly — they don't support file attachments.

Use this workflow when the user says anything like "attach all these reports from my Drive and draft an email."

## Full Pipeline

### Step 1 — Find all documents on Drive

Use `build_service("drive", "v3", service_name=...)` to search. Run multiple queries with different keywords — a single search often misses related files (e.g. "Trustwell" finds Trustwell docs, "Manipal" finds Manipal docs, "Kanta" finds KDR docs). Combine results manually.

**Pattern:**
```python
drive = build_service("drive", "v3", service_name=RESOLVED_SERVICE)
for term in ["Trustwell", "Manipal", "Kanta Ranka", "KDR"]:
    results = drive.files().list(q=f"name contains '{term}'", pageSize=20, fields="files(id, name, mimeType, webViewLink)").execute()
    # Collect and deduplicate by file ID
```

**Categorization:** Group found files into logical categories (Invoices, Reports, Hospitalization Docs, Policy, KYC) to present clearly in the email body.

### Step 2 — Check completeness against the claim

When filing a reimbursement/claim, verify that the invoices on Drive actually cover everything being claimed. Download and inspect invoice PDFs to see line items:

```python
# Download and extract text
request = drive.files().get_media(fileId=FILE_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
# ... loop until done
# Then pdftotext or similar to check line items
```

This catches missing receipts early (e.g. a PFT test that was reported but never invoiced).

### Step 3 — Download and stage locally

Create a temp directory: `/opt/data/<project>_docs/`

Download each file using `drive.files().get_media(fileId=...)` → `MediaIoBaseDownload`. Name files with numbered prefixes so they sort in order:

```
01_WaxRemoval_Invoice.pdf
02_LabTests_Invoice.pdf
...
25_KDR_PAN_CARD.pdf
```

**Deduplicate:** If files are downloaded in multiple batches (e.g. different naming conventions), compare file sizes or hashes before attaching. Same-content duplicates inflate the draft size and waste API quota.

### Step 4 — Build MIME multipart message

**Never use `gws_skill_bridge.draft_create` for attachments** — it does not support them. Use the raw Gmail API:

```python
from tools.gws_auth import build_service
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64

gmail = build_service("gmail", "v1", service_name=SERVICE_NAME)

msg = MIMEMultipart("mixed")
msg["To"] = "..."
msg["Cc"] = "..."
msg["From"] = "..."
msg["Subject"] = "..."

# Body
msg.attach(MIMEText(body_text, "plain", "utf-8"))

# Attachments
for filepath in sorted_file_list:
    with open(filepath, "rb") as f:
        att = MIMEBase("application", "pdf")
        att.set_payload(f.read())
        encoders.encode_base64(att)
        att.add_header("Content-Disposition", "attachment", filename=os.path.basename(filepath))
        msg.attach(att)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
```

**Size limits:** Gmail accepts drafts up to ~35 MB (the max message size is 25 MB for sent messages, but drafts can be slightly larger). If the payload is near this limit, reduce attachment resolution or split into multiple drafts.

**Delete old drafts first** — if a previous version of the same draft exists, delete it before creating the new one to avoid confusion. Search by subject match:

```python
drafts = gmail.users().drafts().list(userId="me", maxResults=10).execute()
for d in drafts.get("drafts", []):
    draft = gmail.users().drafts().get(userId="me", id=d["id"], format="metadata").execute()
    headers = {h["name"]: h["value"] for h in draft["message"]["payload"]["headers"]}
    if target_subject in headers.get("Subject", ""):
        gmail.users().drafts().delete(userId="me", id=d["id"]).execute()
```

### Step 5 — Verify the draft

List drafts to confirm the new one has the right attachment count:
```python
drafts = gmail.users().drafts().list(userId="me", maxResults=5).execute()
for d in drafts.get("drafts", []):
    draft = gmail.users().drafts().get(userId="me", id=d["id"], format="full").execute()
    # Count attachments by inspecting payload parts
```

## Pitfalls

- **Duplicate files from Drive:** Multiple downloads with different naming conventions create duplicate entries in the staging directory. Always compare alternate-named files for same content before attaching both.
- **From address determination:** When the user asks "what email should I send from" for an insurance/legal claim, check the source documents (policy schedule, invoices) for the registered email. If not found on the document, state the gap clearly rather than guessing. The registered mobile on the policy often belongs to the person managing the account.
- **Supplementary docs not on Drive:** KYC docs (PAN, Aadhaar) are often on Drive but other items (Form C, cancelled cheque, NCB certificate) may need to be sourced externally — call/WhatsApp/walk to the bank. List missing items explicitly so the user can collect them.
- **Large Medical Records Compilation files:** These can be 9+ MB each. Multiple large attachments add up fast. 26 PDFs averaging 1 MB each produces a ~27 MB draft which is within limits but close.
