# Google Doc — Create & Populate from Drive Folder Document Analysis

## When to Use

User asks to:
- Analyze all documents in a Google Drive folder
- Create a master summary Google Doc with full narration of each document
- The resulting doc will serve as a knowledge base for a later LLM call (e.g., to draft a sale deed)

## Workflow

### Step 1 — List All Files in the Drive Folder

```python
from tools.gws_auth import build_service

drive = build_service("drive", "v3")

folder_id = "FOLDER_ID_HERE"
results = drive.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    fields="files(id, name, mimeType)",
    pageSize=200
).execute()

files = results.get("files", [])
for f in files:
    print(f["name"], "|", f["id"], "|", f["mimeType"])
```

### Step 2 — Download & Analyze Each Document

**For PDFs:** Render to images + vision_analyze:

```python
import subprocess, os

os.makedirs("/tmp/doc_analysis", exist_ok=True)

# Render PDF pages as PNG
subprocess.run([
    "pdftoppm", "-r", "100", "-png",
    "/path/to/file.pdf",
    "/tmp/doc_analysis/page"
], check=True)

# Or via PyMuPDF (fitz) — better for multi-page:
import fitz
doc = fitz.open("/path/to/file.pdf")
for i, page in enumerate(doc):
    page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(f"/tmp/doc_analysis/page_{i+1}.png")
```

**For Google Docs (Docs/Sheets/Slides):**
```python
# Export as PDF for analysis
request = drive.files().export_media(
    fileId="FILE_ID",
    mimeType="application/pdf"
)
with open("/tmp/exported.pdf", "wb") as f:
    f.write(request.execute())
```

**For `.docx` files:**
```python
from docx import Document
doc = Document("/path/to/file.docx")
text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
```

**For Google Doc already in Drive** (native Google Doc format):
```python
# Use the docs API to get content directly
docs = build_service("docs", "v1")
doc_content = docs.documents().get(documentId="FILE_ID").execute()
# Extract text from doc_content['body']['content']
```

### Step 3 — Vision Analyze for PDF Content

```python
# Images saved at /tmp/doc_analysis/page_*.png
# Call vision_analyze with all pages — join results
```

### Step 4 — Create Google Doc in Target Folder

```python
drive = build_service("drive", "v3")
docs = build_service("docs", "v1")  # Different service!

folder_id = "TARGET_FOLDER_ID"

# Create the Google Doc file
body = {
    "name": "Document Title.doc",
    "mimeType": "application/vnd.google-apps.document",
    "parents": [folder_id]
}
doc = drive.files().create(body=body, media_body=None).execute()
doc_id = doc["id"]
print("Doc ID:", doc_id)
```

**⚠️ Critical: Use TWO different services.** `drive.files().create()` needs the Drive API. `documents().batchUpdate()` needs the Docs API. They are separate endpoints.

### Step 5 — Populate the Doc via BatchUpdate

```python
doc_content = """YOUR_LONG_FORM_CONTENT_HERE"""

content_payload = {
    "requests": [{
        "insertText": {
            "text": doc_content,
            "endOfSegmentLocation": {}
        }
    }]
}

result = docs.documents().batchUpdate(documentId=doc_id, body=content_payload).execute()
print("Doc URL: https://docs.google.com/document/d/" + doc_id + "/edit")
```

**Limitation:** `insertText` appends all content in one shot. For very long documents (>~100KB), split into chunks of ~50,000 characters:

```python
CHUNK_SIZE = 45000
for i in range(0, len(doc_content), CHUNK_SIZE):
    chunk = doc_content[i:i+CHUNK_SIZE]
    docs.documents().batchUpdate(documentId=doc_id, body={
        "requests": [{"insertText": {"text": chunk, "endOfSegmentLocation": {}}}]
    }).execute()
```

### Step 6 — Share the Doc

The `webViewLink` in the file resource is the shareable link:
```python
file = drive.files().get(fileId=doc_id, fields="webViewLink").execute()
print(file["webViewLink"])
```

## Verified Pattern for This Session (DRA Thindlu Land Partners)

```
Folder: https://drive.google.com/drive/folders/10sk0X6dq9-Rzo2BajJKNFkEts_pfRxLT
Result: https://docs.google.com/document/d/1kGw6nzq6QVjTnoWgUR-TfYtE6V1INqukOOkBcNe8VoQ/edit
```

## Pitfalls

1. **`drive.documents()` doesn't exist.** The Drive API (`drive.files()`) creates the file, but the Docs API (`docs.documents()`) edits content. Always import `build_service("docs", "v1")` separately.

2. **Chunk long content.** Google Docs API has a limit per `insertText` call. Split content into ~45,000 char chunks for safety.

3. **File name collision.** If a doc with the same name already exists in the folder, `drive.files().create()` creates a new one (with "(1)" appended). Check first or use unique naming with timestamp.

4. **OAuth scope.** The current session user must have write access to the target folder. If the token only has Calendar scope, Drive operations fail with 403. Refresh with explicit Drive scope before Drive operations.