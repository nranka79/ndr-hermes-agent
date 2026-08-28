# HTML-to-PDF Generation

Generate professional PDFs from HTML content when the user needs a presentable document with tables, colors, and formatting.

## WeasyPrint (Recommended)

```python
from weasyprint import HTML

# From HTML string
HTML(string='<html><body><h1>Hello</h1></body></html>').write_pdf('/path/to/output.pdf')

# From HTML file
HTML('file.html').write_pdf('/path/to/output.pdf')
```

**Install:** `uv pip install weasyprint`

**CSS for A4 output:**
```css
@page {
  size: A4;
  margin: 2cm 2.2cm;
}
body {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.5;
  color: #222;
}
```

### What Works Well
- Full CSS support (colors, borders, backgrounds, tables)
- Font styling (bold, italic, colors, sizes)
- Complex tables with alternating row colors
- Hyperlinks (clickable in the PDF)
- Page numbers via `@page` rules
- Unicode text (em-dashes, arrows, accents)

### Key Tips
- Use **inline styles** rather than CSS classes for critical formatting (more reliable)
- Set `@page { size: A4; ... }` for proper page dimensions
- Use `<table cellpadding="4" cellspacing="0">` for clean table spacing
- Verify page count with `pdfinfo` command after generation

## Google Doc Export to PDF

When the content is already in a Google Doc:

```python
import io
from googleapiclient.http import MediaIoBaseDownload

pdf_bytes = io.BytesIO()
request = drive.files().export_media(fileId=DOC_ID, mimeType='application/pdf')
downloader = MediaIoBaseDownload(pdf_bytes, request)
done = False
while not done:
    status, done = downloader.next_chunk()

# Save or attach directly
with open('output.pdf', 'wb') as f:
    f.write(pdf_bytes.getvalue())
```

## Quick Page Count Verification

```bash
pdfinfo /path/to/output.pdf | grep -E "Pages|Page size"
```

## Pitfalls

- **fpdf2** (alternative library) has severe Unicode limitations with built-in fonts — can't render bullet characters, em-dashes, arrows. Use weasyprint instead.
- **ReportLab** is powerful but verbose for document-style PDFs. Stick with weasyprint for HTML-to-PDF workflows.
- **Large HTML files** (>50KB) may take 5-10 seconds to render with weasyprint. Normal for complex documents.
- **WeasyPrint may not be pre-installed** — install via `uv pip install weasyprint` first.
- **Google Doc export as PDF** produces a PDF from whatever the doc currently looks like, including any uncollapsed table-of-contents or comments.
