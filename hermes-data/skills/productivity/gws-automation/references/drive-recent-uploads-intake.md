# Drive Recent Uploads Intake — Scanned Document Batch Processing

## Trigger
User says "I have just added [N] files/documents to the Drive" or "look in recent files" — they've uploaded Adobe Scan PDFs (or other scanned documents) to Drive root (or a generic location) and want them examined, renamed, and filed into the correct folders.

## Key Difference from Folder-Based Intake
The existing `drive-document-intake-pipeline.md` assumes a **designated folder** to scan. This workflow starts from **no specific folder** — the user uploaded directly to Drive root or a shared parent, and you must find the files via recency.

## Step 1 — Find Recently Uploaded Files

List PDFs ordered by modifiedTime descending. Limit to PDF mimeType to exclude Google-native files:

```python
results = drive.files().list(
    q="mimeType='application/pdf' and trashed=false",
    orderBy='modifiedTime desc',
    pageSize=15,  # generous for the user's batch
    fields='files(id, name, modifiedTime, size)'
).execute()
```

**What to look for:** Files with the SAME modifiedTime (within seconds) are the batch the user just uploaded. Adobe Scan produces names like `Adobe Scan DD MMM YYYY.pdf` and `Adobe Scan DD MMM YYYY (N).pdf`.

**Cross-reference with user's stated count:** The user said "N files" — verify the matched batch has N files. If fewer, some may be from a different conversation or were uploaded via a different mechanism.

## Step 2 — Download for Examination

Download to a local temp directory:

```python
import io
from googleapiclient.http import MediaIoBaseDownload

fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, drive.files().get_media(fileId=fid))
done = False
while not done:
    status, done = downloader.next_chunk()

with open(f'/tmp/intake/{fname}', 'wb') as f:
    f.write(fh.getvalue())
```

Use `/opt/data/drive_downloads/` or `/tmp/` as the local staging directory.

## Step 3 — Examine Content (Scanned PDFs)

Adobe Scan PDFs are **image-based** (scanned photos). Use fitz to check for text layer:

```python
import fitz
doc = fitz.open(local_path)
total_chars = sum(len(page.get_text()) for page in doc)
# If < 100 chars → image-only scanned PDF
```

**For image-only PDFs** (most Adobe Scans), render each page to PNG and use `vision_analyze`:

```python
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=250)
    pix.save(f'/tmp/img/{base}_p{i+1}.png')
```

Then call `vision_analyze(image_url='/tmp/img/xxx_p1.png')` for each page to OCR the content.

**For text-based PDFs**, use pdftotext or fitz `.get_text()` directly.

## Step 4 — Identify Each Document

From the OCR text, extract:
- **Patient/Person**: Name appears in headers ("Mr. NISHANT RANKA", "Mrs. KANTA RANKA", etc.)
- **Hospital**: Trustwell Hospital, Manipal Hospital, etc.
- **Doctor**: Dr. Deepak Haldipur, etc.
- **Document type**: Audiological Evaluation Report, Bill of Supply, Lab Prescription, etc.
- **Date**: From the document header or bill date
- **Amounts**: For invoices/bills

### Typical Document Types from a Single Consultation Visit
| Type | What to Look For |
|---|---|
| **Audiological Evaluation Report** | "Audiological Evaluation Report" header, audiogram chart, PTA values |
| **Lab/Prescription Sheet** | "Hb%, CBC, Platelet Count, PT/INR..." test lists, doctor's name |
| **OP Consultation Invoice** | "Bill of Supply", "OP CONSULTATION", consultation fee (₹900-₹1,500) |
| **Procedure Invoice** | "Bill of Supply", procedure name + amount (e.g., "Microscopic Wax Removal" + "Pure Tone Audiometry") |
| **Lab Tests Invoice** | "Bill of Supply", itemised test list (ECG ₹500, HbA1c ₹1,210, etc.) |

## Step 5 — Separate by Patient / Category

Documents from the same upload batch may involve **different people** or **different categories**:
- **NDR Medical**: Nishant's ENT consultation documents
- **KDR Medical**: Kanta Ranka's (mom) ENT consultation documents  
- **Other legal/non-medical**: WILL deeds, property docs, etc. — flag these to the user

**Check each file's patient name** — don't assume the batch is uniform. The user may have scanned both their own and their family member's documents together.

## Step 6 — Rename Per Convention

Format: `YYYYMMDD_Patient_DocumentType_Hospital_Details.pdf`

Examples from this session:
```
20260709_NDR_AudiologicalEvaluation_Trustwell.pdf
20260709_NDR_LabTests_Prescription_Trustwell.pdf
20260709_NDR_OPConsultation_Invoice_Trustwell.pdf
20260709_KDR_AudiologicalEvaluation_Trustwell.pdf
20260709_KDR_LabTests_Prescription_Trustwell.pdf
20260709_KDR_WaxRemoval_PTA_Invoice_Trustwell.pdf
20260709_KDR_LabTests_Consultation_Invoice_Trustwell.pdf
```

## Step 7 — Move to Target Folders

```python
drive.files().update(
    fileId=fid,
    body={'name': new_name}
).execute()

# Get current parents, then move
current_parents = ','.join(file_info.get('parents', []))
if current_parents:
    drive.files().update(
        fileId=fid,
        addParents=target_folder_id,
        removeParents=current_parents
    ).execute()
```

**Known medical folder IDs (Nishant's Drive):**
| Folder | ID |
|---|---|
| NDR Medical | `0B1Oc8cSaJXPGT1JPMVlfajFnTmc` |
| KDR Medical | `0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s` |
| DR Medical | `0B1Oc8cSaJXPGRXFWMnhuYmlXUDg` |
| DDR Medical | `1cLMGwITTiCJUykA0iMVZ_vMNMbuyVr2n` |

## Step 8 — Handle Non-Medical Files in Batch

When a non-medical document (WILL, deed, property document) is uploaded alongside medical files, flag it to the user with:
- What the document is
- Where it currently sits (still in Drive root)
- Where they might want it filed (Legal folder, Personal folder, etc.)

Do NOT move it without explicit direction.

## Vault Auth for This Workflow

Nishant's vault user_id is `ndr-<telegram-id>` (compound: `draas_user_id` + `-` + `telegram_id`). Use direct vault socket access to get the `google-draas` token (has Drive scope):

```python
VAULT_SOCKET = '/run/gws-vault/vault.sock'

def get_token(user_id, service):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(VAULT_SOCKET)
    req = json.dumps({'op':'get','user_id':user_id,
                      'service':service,'session_uid':user_id})
    sock.sendall((req + '\n').encode())
    resp = b''
    while b'\n' not in resp:
        chunk = sock.recv(65536)
        if not chunk: break
        resp += chunk
    sock.close()
    result = json.loads(resp.decode())
    if result.get('ok'):
        return json.loads(result['token_json'])
    raise RuntimeError(f"Vault error: {result.get('error')}")

token_data = get_token('ndr-<telegram-id>', 'google-draas')
creds = Credentials.from_authorized_user_info(token_data)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
drive = build('drive', 'v3', credentials=creds)
```

## Common Pitfalls

- **Fitz `page_count` read after `doc.close()`** raises `ValueError('document closed')`. Close after reading the page count, not before.
- **files from different dates in the same batch** — Adobe Scan timestamps reflect when the scan was taken, but all upload to Drive at the same time. The `modifiedTime` in Drive reflects the upload moment, not the scan date. Check the document's internal date.
- **WILL / legal documents mixed in with medical** — The user may scan unrelated documents at the same time. Identify and separate.
- **Voice message about the upload may be garbled** — The garbled transcription's intent is best inferred from the document content itself, not from the voice note text.
