# Signed Document Receipt & Filing

When the user sends scanned PDFs of signed/executed physical documents (courier/post), follow this workflow.

## Trigger

User sends scanned PDFs via chat with instructions like:
- "Rename and file these in the appropriate Drive folder"
- "These are signed copies of [agreement name] from [party]"
- "File these in the legal/title documents folder"

## Workflow

### Phase 1: Identify the documents

The user typically sends multiple PDFs in one message batch:
1. **Covering letter** — usually small file (100-300KB), identifies sender, date, context
2. **Signed agreement copy 1** — large scanned file (5-10MB), for DRAAS records
3. **Signed agreement copy 2** — large scanned file (5-10MB), to be returned to sender

Use `vision_analyze` for OCR on image-based PDFs (convert with `pdftoppm` first):
```bash
pdftoppm -jpeg -r 200 input.pdf /tmp/output_prefix
```

### Phase 2: Extract key details

From the covering letter:
- Sender name and address
- Date of letter
- Document being sent (agreement type, date)
- Any instructions (countersign, return copy)

From the signed agreement:
- Document title and date
- All parties (landowners, developer, signatories)
- Signature blocks (who signed, witness details)

### Phase 3: Rename files

Follow YYYYMMDD_DescriptiveName convention:

| Document | Naming Pattern | Example |
|----------|---------------|---------|
| Covering letter | `YYYYMMDD_SenderName_CoveringLetter_ProjectName_DocumentType.pdf` | `20260714_RaghuIyer_CoveringLetter_RankaAmber_SSA.pdf` |
| Signed copy (our copy) | `YYYYMMDD_ProjectName_AgreementType_Signed_Copy_For_DRA.pdf` | `20260624_RankaAmber_SupplementarySharingAgreement_Signed_Copy_For_DRA.pdf` |
| Signed copy (to return) | `YYYYMMDD_ProjectName_AgreementType_Signed_Copy_For_Sender.pdf` | `20260624_RankaAmber_SupplementarySharingAgreement_Signed_Copy_For_Raghu.pdf` |

### Phase 4: Identify target folder

**ALWAYS confirm the folder with the user before filing.** User explicitly states preference: "confirm the folder where you're filing them."

**User's preferred project folder hierarchy (Jul 2026, corrected by Nishant):**
```
[Project Name] - [Location]/
├── Title Documents/    ← signed agreements, title deeds, legal docs
├── Approvals/          ← plan sanctions, RERA, BBMP
├── Marketing/          ← brochures, renders
└── ...
```

Examples of correct project root folders:
- `Ranka Amber` (root level, ID: `1pr8qQDrQYPC1PK7T4ZIJJY-iYjy3noe5`) — correct, has `Title Documents` subfolder
- `Ranka Amber - Whitefield` (under `Amber` umbrella, ID: `1Y2UFlSieN16TFdlQgb9tsQOUBMTCnNGr`) — **owned externally**, NOT writable

**What to check FIRST — where does the project folder exist?**
- Root-level project folder (e.g., `Ranka Amber`, `Ranka Oasis`) — usually writable by ndr@draas.com
- Under `Current Properties` or `Amber` umbrella — may be owned externally

When the user says "title documents" or "legal folder," search for:
1. `[Project Name] > Title Documents` — **preferred structure** (create subfolder if missing)
2. `[Project Name] - [Location] > Project Legal Documents` — alternative (check writability)
3. Root-level `RANKA AMBER DOCUMENTS` etc. — **last resort**, these are incorrect per user (Jul 2026). This was a catch-all folder; use `[Project Name] > Title Documents` instead.

**Before filing, verify write access:**
```python
f = service.files().get(fileId=folder_id, fields='id, name, capabilities').execute()
if f['capabilities'].get('canAddChildren'):
    # Can upload
else:
    # Cannot upload — tell user, create Title Documents under the root-level project folder
```

**Known permission quirks for DRAAS folders (Jul 2026):**
- `Ranka Amber - Whitefield` (ID: `1Y2UFlSieN16TFdlQgb9tsQOUBMTCnNGr`) — **NOT writable** by ndr@draas.com (owned externally)
- `Project Legal Documents` (subfolder of above) — **NOT writable** by ndr@draas.com
- `RANKA AMBER DOCUMENTS` (root level, ID: `1HmCPlVkdjAvoxGYTZwOShmfl3yykWR1j`) — writable but **INCORRECT** location per user (Jul 2026).
  Use `Ranka Amber > Title Documents` instead.
- `Ranka Amber` (root level, ID: `1pr8qQDrQYPC1PK7T4ZIJJY-iYjy3noe5`) — **writable**, correct project root.
  Subfolder `Title Documents` (ID: `1VNYPHO7xFJLzdumxCoT9e1ML-gbPrbob`) created Jul 2026.

**If the user-specified folder isn't writable:** tell the user explicitly and suggest creating a `Title Documents` subfolder under the root-level project folder. Do NOT file in a catch-all root-level folder without user confirmation.

### Phase 5: Upload

Use `terminal()` (not `execute_code`) for all GWS operations — the vault socket is only available in the terminal environment:

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools import gws_auth
from googleapiclient.http import MediaFileUpload

service = gws_auth.build_service('drive', 'v3', service_name='google-draas')
media = MediaFileUpload(local_path, mimetype='application/pdf', resumable=True)
result = service.files().create(
    body={'name': filename, 'description': desc, 'parents': [target_folder], 'mimeType': 'application/pdf'},
    media_body=media,
    fields='id, name, webViewLink, size'
).execute()
```

### Phase 6: Check stakeholder access

Before sending WhatsApp notification, verify the stakeholder already has access to the target folder:

```python
try:
    perms = service.permissions().list(fileId=folder_id, fields='permissions(id, type, emailAddress, role)').execute()
    for p in perms.get('permissions', []):
        if p.get('emailAddress') == stakeholder_email:
            # Already has access — no changes needed
except:
    # Permission read may fail if user doesn't have permission to list perms
    # Grant viewer access proactively
    service.permissions().create(
        fileId=folder_id,
        body={'type': 'user', 'role': 'reader', 'emailAddress': stakeholder_email},
        sendNotificationEmail=False
    ).execute()
```

Known access for key DRAAS stakeholders on RANKA AMBER DOCUMENTS folder:
- Bharat (sales1.blr@draas.com) — **owner**
- Prakash Singh (psingh@draas.com) — check
- Roshni (rnr@draas.com) — **writer**
- Eshwari (echamundeshwari@draas.com) — check

### Phase 7: Notify stakeholder

The WhatsApp link tool (`whatsapp_link`) may not be available. If unavailable, provide the Drive link(s) directly to the user to forward, along with a ready-to-forward message.

Message format:
> Bharat — the signed [Agreement Name] for [Project] ([Parties]) has been filed. Here's the link:
> [Drive link for the DRA copy]
> It's in the [Folder Name] folder which you already have access to as [role]. Let me know if you need anything else.

### Phase 8: Remind user of next steps

If the covering letter requests further action (e.g., "countersign and return one copy"), remind the user:
- Countersign both copies
- Return one to the sender (courier/post)
- Keep one for DRAAS records

## Variant: Digital Return (User uploads signed PDF via chat)

When the user **digitally signs and re-uploads a PDF** that *you created for them* (e.g., shorter notice, consent letter), the workflow differs:

### Differences from physical-courier flow

| Approach | Physical Courier | Digital Return |
|----------|-----------------|----------------|
| Source of signed doc | Scanner/courier PDF via chat | User uploads back the PDF you previously generated |
| OCR needed | Yes (scanned image PDF) | No (text-layer PDF already) |
| File naming | YYYYMMDD_Sender_Description | YYYYMMDD_Entity_DocumentType_Signed.pdf |
| Target folder | Project > Title Documents | Shareholder Matters > Entity > BM |
| Notification | WhatsApp to stakeholder | Draft email reply on existing thread with signed PDF attached |
| Recipient | Single stakeholder | Compliance, Balaji, directors on thread |

### Additional steps for Digital Return

1. **Get the original email thread** — search Gmail for the relevant subject (e.g., "Board Meeting - 22nd August 2026")
2. **Copy all original recipients** (To + Cc) from the thread
3. **Add Balaji** (balaji.n@drahomes.in) in Cc — he's the compliance point of contact
4. **Create a drafted reply** (NEVER send autonomously) with the signed PDF attached, threaded via In-Reply-To + References headers

### Draft email recipe (raw MIME, threaded)

```python
import sys, base64
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import _load_credentials_direct
from googleapiclient.discovery import build
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

creds = _load_credentials_direct('google-draas')
svc = build('gmail', 'v1', credentials=creds)

msg = MIMEMultipart('mixed')
msg['To'] = 'compliance@drahomes.in'
msg['Cc'] = ','.join(original_cc_list)
msg['Subject'] = f'Re: {original_subject}'
msg['In-Reply-To'] = '<original_message_id>'
msg['References'] = original_references + ' <original_message_id>'
msg['From'] = 'Nishant Ranka <ndr@draas.com>'

body = MIMEText('''Dear Compliance and Balaji,

Please find attached the signed [Document Name].

Kindly acknowledge receipt.

Warm Regards,
Nishant Ranka
Director
''', 'plain')
msg.attach(body)

with open(local_pdf_path, 'rb') as f:
    pdf_data = f.read()
attachment = MIMEBase('application', 'pdf')
attachment.set_payload(pdf_data)
encoders.encode_base64(attachment)
attachment.add_header('Content-Disposition', 'attachment', filename=signed_filename)
msg.attach(attachment)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
draft = svc.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw, 'threadId': thread_id}}
).execute()
print(f"Draft: {draft['id']}")
```

### Filing location for corporate governance docs

For corporate/company documents (consent letters, shorter notices, board meeting resolutions), the target is **not** a project Title Documents folder but:

```
Shareholder Matters/
├── [Entity Name]/ 
│   ├── BM/       (Board Meeting notices, shorter-notice consents, minutes)
│   ├── AGM/      (Annual General Meeting docs)
│   ├── EGM/      (Extraordinary General Meeting docs)
│   └── Minutes/  (general minutes)
```

To find the right entity subfolder under Shareholder Matters:
```python
svc.files().list(
    q="'<SHAREHOLDER_MATTERS_ID>' in parents and mimeType='application/vnd.google-apps.folder'",
    fields='files(id,name)'
)
```

### Verification steps

- Verify the signed PDF is not distorted via `pdftoppm` + `vision_analyze`
- Check the draft was created by confirming the draft ID in the output
- Report the Drive link + draft status to the user ("Draft ready in your Gmail Drafts folder")

## Pitfalls

- **`drive_v3.files().media_upload()` does NOT exist** — use `files().create()` with `media_body` parameter instead
- **`execute_code` sandbox cannot access GWS vault** — always use `terminal()` for GWS operations
- **'InsufficientPermissionsForParent' error** — check `capabilities.canAddChildren` before attempting upload to a folder
- **Covering letter is a separate document** — don't merge it with the agreement; file it separately alongside the agreement
- **Two signed copies are often identical** — name them distinctly (Copy_For_DRA vs Copy_For_Sender) so the user knows which is which
- **WhatsApp link tool may not be available** — cannot generate wa.me links; provide the raw Drive link to the user to forward
