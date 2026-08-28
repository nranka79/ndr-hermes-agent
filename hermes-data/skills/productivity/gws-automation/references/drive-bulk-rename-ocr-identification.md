# Drive Bulk Rename — OCR Identification of Unnamed PDFs

**Trigger:** User shares a Drive folder link containing unnamed timestamp-only PDFs (e.g. `202606041752.pdf`, `202606041753.pdf`, `Ack for DDs.pdf`, `Email.pdf`) and asks "rename all files which are not properly named."

## Workflow

### Step 1 — List and Identify Targets

List folder contents, filter for files with no descriptive name:

```python
children = drive.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    fields='files(id, name, mimeType, size)',
    orderBy='name'
).execute()
items = children.get('files', [])

# Identify unnamed files — typically:
#   - Timestamp-only names: 202606041752.pdf (YYYYMMDDHHMM.pdf)
#   - Generic names: Ack for DDs.pdf, Email.pdf, Scan.pdf, Doc.pdf
unnamed = [f for f in items if not is_descriptive_name(f['name'])]
```

### Step 2 — Download & OCR Each File

Use the **pdftoppm + tesseract** pipeline (works when OpenRouter vision credits are exhausted):

```python
import tempfile, subprocess

resp = drive.files().get_media(fileId=fid).execute()
tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
tmp_pdf.write(resp)
tmp_pdf.close()

# Convert first page to PNG
subprocess.run([
    'pdftoppm', '-png', '-r', '150', '-f', '1', '-l', '1',
    tmp_pdf.name, '/tmp/page'
], capture_output=True, timeout=30)

# OCR with tesseract
result = subprocess.run(
    ['tesseract', '/tmp/page-1.png', '-', '-l', 'eng'],
    capture_output=True, text=True, timeout=30
)
text = result.stdout.strip()[:400]
```

### Step 3 — Identify Document From OCR Output

Scan the OCR text for:
- **Document type keywords:** "Sale Deed", "NOC", "No Objection", "Khatha", "Loan Closure", "Receipt", "Allotment Letter", "Memorandum of Deposit", "Title Deed", "Vacating", "Acknowledgement", "Representations & Warranties"
- **Parties:** Look for names like "Ravikumar Kubasing Naik", "Nishant Ranka", "Roshni Ranka"
- **Dates:** Look for date strings in the text (e.g. "4th day of June 2026", "10/03/2026")
- **Project/Property:** "Flat No. 914", "Embassy Habitat", etc.

### Step 4 — Rename Following Convention

Standard naming convention: `YYYYMMDD_Project_PrincipalParty_Description.pdf`

```python
renames = {
    '202606041752.pdf': '20260604_914EH_RavikumarKNaik_SellersRepresentationsWarranties.pdf',
    '202606041753.pdf': '20260603_914EH_RavikumarKNaik_NOC_FromSeller.pdf',
    'Ack for DDs.pdf': '20260604_914EH_RavikumarKNaik_Acknowledgement_DemandDrafts.pdf',
    # etc.
}

for old_name, new_name in renames.items():
    drive.files().update(fileId=name_to_id[old_name], body={'name': new_name}).execute()
```

### Rename Tips

- **Date comes from document content**, not just the filename timestamp. A file named `202606041754.pdf` (uploaded at 17:54 on Jun 4) may contain a document dated 2016.
- **Duplicate content versions:** Files named `Name (1).pdf` alongside `Name.pdf` with different sizes are different documents — OCR both.
- **File extension stays the same** — `.pdf` stays `.pdf`, `.jpg` stays `.jpg`.

## Common Document Patterns Found in 914 EH Session

| OCR Signal | Likely Document | Typical Date Source |
|---|---|---|
| "Seller's Declaration of Representations & Warranties" | Representations & Warranties Deed | Near top: "made on the X day of Month YYYY" |
| "NO OBJECTION CERTIFICATE" | NOC from Seller | Below title |
| "KHATHA EXTRACT" / "ಕಥಾ ಸಾರ" | BBMP Khatha Certificate | In header block |
| "CLOSURE OF HOUSING LOAN" / "Loan Closure Certificate" | Bank Loan Closure Letter | In letter body |
| "cleared all Common Area Maintenance" | Society No Dues Certificate | In body text |
| "vacated the premises" | Tenant Vacating Letter | From date in letter |
| "Original Allotment Letter" | Embassy/Builders Allotment | At top or in header |
| "Master Originals Handover Receipt" | Document Handover Receipt | At top |
| "MEMORANDUM RELATING TO DEPOSIT OF TITLE DEED" | Mortgage/Title Deed Deposit | Opening clause |
| "ACKNOWLEDGEMENT OF RECEIPT OF DEMAND DRAFTS" | DD Acknowledgement | At top |
| Email header lines ("From:", "To:", "Subject:") | Email Print / PDF | Header date |

## Pitfalls

- **fitz returns empty on scanned PDFs** — always use the pdftoppm + tesseract fallback for legal/registered documents
- **Large PDFs (>5MB)** need more time for pdftoppm + tesseract — set timeout ≥120s
- **Duplicate files:** After renaming, list the folder again to verify — batch rename operations on Drive are idempotent
- **Page 1 only is enough** for identification — no need to OCR the full document
- **(1) suffixed files** are usually NOT duplicates — check size before deciding
