# WeasyPrint HTML → PDF Generation

Use when the user wants a **professional, formatted PDF** — medical dossiers, legal documents, reports, pitch decks. WeasyPrint renders HTML/CSS to PDF with full page-break, table, and color support.

## Installation

```bash
uv pip install weasyprint
```

## Basic Pattern

```python
from weasyprint import HTML

html_content = """<!DOCTYPE html>
<html><head>
<style>
@page {
  size: A4;
  margin: 2cm 2.2cm;
}
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.5; }
h1 { font-size: 18pt; color: #1c5499; border-bottom: 2px solid #1c5499; }
h2 { font-size: 14pt; color: #1c5499; margin-top: 22px; }
table { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin: 8px 0; }
table th { background: #1c5499; color: white; padding: 5px 8px; }
table td { padding: 4px 8px; border: 1px solid #ccc; }
table .highlight td { background: #dce6f5; font-weight: bold; }
.highlight-box { background: #fff4dc; border: 1.5px solid #c8a030; padding: 10px 14px; }
</style></head>
<body>
<!-- content -->
</body></html>"""

HTML(string=html_content).write_pdf('/path/to/output.pdf')
```

## Key CSS Techniques for Medical/Legal Documents

### A4 Page Setup
```css
@page {
  size: A4;
  margin: 2cm 2.2cm;
}
```

### Dashboard-Style Data Table
```css
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9.5pt;
}
table th {
  background: #1c5499;  /* Navy header */
  color: white;
  padding: 5px 8px;
  text-align: left;
}
table td {
  padding: 4px 8px;
  border: 1px solid #ccc;
}
table tr:nth-child(even) td {
  background: #f7f9fc;  /* Alternating row color */
}
```

### Highlighted Key Feature Box
```css
.highlight-box {
  background: #fff4dc;
  border: 1.5px solid #c8a030;
  border-radius: 6px;
  padding: 10px 14px;
  margin: 12px 0;
  font-weight: bold;
  color: #b0321e;
}
```

### Side-by-Side Views (Neutral Comparison)
```css
.view-a {
  background: #fff8f0;
  border-left: 4px solid #c8a030;
  padding: 8px 12px;
}
.view-b {
  background: #f0f6ff;
  border-left: 4px solid #1c5499;
  padding: 8px 12px;
}
```

### Page Numbering in Footer
```css
@page {
  @bottom-center {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 8pt;
    color: #888;
  }
}
```

## Drive Upload + Sharing

After generating the PDF, upload to Drive and set permissions:

```python
from googleapiclient.http import MediaFileUpload
from gws_auth import build_service

drive = build_service('drive', 'v3', telegram_id='USER_TG_ID')
media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
body = {
    'name': 'Document_Name_Date.pdf',
    'parents': [FOLDER_ID],
    'description': 'Description'
}
uploaded = drive.files().create(body=body, media_body=media, fields='id,name,webViewLink').execute()
drive.permissions().create(
    fileId=uploaded['id'],
    body={'type': 'anyone', 'role': 'reader'},
    fields='id'
).execute()
drive_link = uploaded['webViewLink']
```

## Delivering via Telegram

Send with `MEDIA:` prefix in send_message:

```python
send_message(message=f"MEDIA:{pdf_path}", target="telegram")
```

## Pitfalls

- **Unicode characters** (▸, ❌, ⏳, →) are NOT supported by PDF built-in fonts (Helvetica, Times, Courier). Use HTML entities (`&rarr;`), simple dashes (`-`), or Unicode TTF fonts.
- **multi_cell in fpdf2** can't handle text after a `cell()` with `ln=0` at certain x-positions — use WeasyPrint HTML/CSS instead for complex layouts with mixed text and tables.
- **WeasyPrint page breaks** happen naturally — no need for `page-break-before` unless you want a forced section break at a specific point.
- **Clickable links** in WeasyPrint PDFs work when rendered as `<a href="...">` in the HTML. Test links open in the PDF viewer.
