# Google Doc Formatting Verification Loop

After creating/formatted a Google Doc via HTML import or Docs API, you often need to **visually verify** the layout — margins, justification, spacing, page breaks — before delivering to the user. Since you cannot open Google Docs in a browser (login walls), use this offline verification loop.

## The Loop

```
Create/fix doc via Drive/Docs API
  → Export as PDF via Drive API
  → Convert PDF pages to PNG via pdftoppm
  → vision_analyze on each page image
  → Detect formatting issues
  → Fix via Docs API batchUpdate
  → Re-export → repeat until satisfied
```

## Step-by-step

### 1. Export Google Doc as PDF

```python
import io
from googleapiclient.http import MediaIoBaseDownload

drive = build_service("drive", "v3")
request = drive.files().export(fileId=DOC_ID, mimeType="application/pdf")
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open("/tmp/letter.pdf", "wb") as f:
    f.write(fh.getvalue())
```

### 2. Convert PDF to PNG pages

```bash
# Install poppler-utils if pdftoppm is missing
# sudo apt install poppler-utils -y

pdftoppm -png -r 200 /tmp/letter.pdf /tmp/letter_preview
# Produces: letter_preview-1.png, letter_preview-2.png, ...
```

- `-r 200` = 200 DPI (good balance of quality/speed)
- Each page becomes a separate PNG

### 3. Vision analysis on each page

```python
# Call vision_analyze for each page image
vision_analyze(
    image_url=f"/tmp/letter_preview-{page}.png",
    question="Analyze the formatting: ..."
)
```

**What to ask about (pick relevant checks):**
- Margins — are they consistent (1 inch / 2.54cm on all sides)?
- Text justification — is body text fully justified?
- Line spacing — does it look like 1.5 spacing or single?
- Section headings — are they bold and clearly separated?
- Page breaks — does content break cleanly or orphan a heading at page bottom?
- Font — does it match the expected font family?
- Letterhead — centered properly with separator line?
- Tables — do they render with borders and background colors?

### 4. Fix issues via Docs API

Based on vision findings, use `documents().batchUpdate()` to fix:

```python
docs = build_service("docs", "v1")
docs.documents().batchUpdate(
    documentId=DOC_ID,
    body={"requests": [
        # Fix alignment, spacing, bold, font size, etc.
    ]}
).execute()
```

### 5. Loop

Re-export the PDF and re-run vision analysis. The PDF is regenerated from the live doc, so fixes are reflected.

## What to check per document type

| Document Type | Key formatting checks |
|---|---|
| Formal legal letter | 1" margins, justified body, Times New Roman, 1.5 line spacing, bold subject, centered letterhead, signature block |
| Agreement / Deed | Section headings bold, paragraph indentation hierarchy, pure black text, no bullets on numbered clauses |
| Presentation / Brochure | Table borders visible, background colors preserved, image alignment, font sizes hierarchy |
| Internal memo | Clean sans-serif font, clear subject line, bullet list consistency, signature close |

## Pitfalls

- **`vision_analyze` only does OCR for most models** — it can extract text but may not give detailed visual layout feedback. Frame questions about LAYOUT (spacing, alignment, margins) not just content.
- **PDF export is rasterized** — the PDF from Drive may not perfectly match what Google Docs renders in-browser (subtle font differences possible). Consider it a "good enough" approximation.
- **Multi-page PDFs** — convert all pages and check the critical ones (page 1 for first impression, last page for signature block, any page with tables).
- **Large documents** — 20+ page PDFs → only convert and check the first/last pages and any page with complex formatting (tables, special sections).
- **`pdftoppm` may not be installed** — check with `which pdftoppm` first. Install via `sudo apt install poppler-utils -y` if missing.
- **Temporary files** — clean up PNGs and PDFs after verification to avoid cluttering the filesystem.
