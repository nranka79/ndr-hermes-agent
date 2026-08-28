# Resume from Drive — Search, Download & Extract

When the user says the candidate's resume is on Drive (or "it's in the recruitment folder, pull it from there"), follow this workflow.

## 1. Search Drive

Always use the user's OAuth token via `gws_auth.build_service('drive', 'v3')` for Drive searches. The SA (`gws_sa`) may not have access to user-specific folders like the DRA Recruitment folder.

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

# Search by candidate name
results = drive.files().list(
    q="name contains 'Romy'",
    fields='files(id, name, webViewLink)',
    pageSize=50
).execute()
```

**Primary locations to search (in order):**
- **DRA Recruitment folder** — `1wHFU4pv7-h6_OZYx678R_LTcf1jOteoZ` — active candidate resumes (PDFs from various sources). Filter with: `"'{folder_id}' in parents and name contains 'Name'"`
- **naukri resumes folder** — `1u9yYBsnkfAFpPELRDTspg00xQxluQ20-` — Naukri-sourced resumes only
- **Full Drive search** — `"fullText contains 'Candidate Name'"` — broadest, catches emails mentioning them too

If the resume filename has a date suffix like `260615_190230`, it's 20YYMMDD_HHMMSS format.

## 2. Download the PDF

```python
# Download by file ID
file_id = '1oDKPZm6gVO8XGgOdTYprfqEDkeHjwbZd'
fh = drive.files().get_media(fileId=file_id).execute()
with open('/tmp/candidate_resume.pdf', 'wb') as f:
    f.write(fh)
```

## 3. Extract text

`pdftotext` is reliably available (from poppler-utils). Use it for text-based PDFs:

```shell
pdftotext /tmp/candidate_resume.pdf -
```

This outputs plain text to stdout. For scanned/image PDFs, fall back to OCR (tesseract or vision_analyze).

```python
import subprocess
result = subprocess.run(['pdftotext', '/tmp/candidate_resume.pdf', '-'],
                       capture_output=True, text=True)
text = result.stdout
```

## 4. Use extracted content

Map resume content to offer letter sections:
- **Opening paragraph** — education (degree, CGPA, institution), relevant experience, key skills mentioned in user's voice messages. Confirm the personalisation level with the user (brief welcome vs resume-anchored).
- **Primary Responsibilities** — bridge sentence connecting their background to the role.
- **KPIs** — borrow role-specific language from the resume (e.g. ERP exposure → ERP adoption KPI).

## Pitfalls

- **Voice transcription vs resume** — user says "Rome" via voice but resume says "Romy". The resume file is the authoritative source. Flag discrepancies before sharing the draft.
- **PDF with tracking/watermark** — some Naukri resumes have caller-watermarks; the text is still extractable by pdftotext.
- **No pymupdf** — `fitz` (pymupdf) is not installed by default. Don't attempt import; use `pdftotext` directly.
- **GOOGLE_SA_KEY not inherited** — the SA key env var from the Hermes agent process is NOT available in terminal() subprocesses. Always use `gws_auth.build_service()` (user's OAuth) for Drive searches during offer letter preparation, not `gws_sa`.
