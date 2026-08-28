# Editing .docx Files on Google Drive with python-docx + Visual Verification

When a user has a .docx file on Google Drive (not a native Google Doc) and needs formatting fixes, line spacing changes, or text replacements — while keeping the same file ID and link — use this workflow.

## The Workflow

### 1. Download the .docx from Drive

```python
from googleapiclient.http import MediaIoBaseDownload
import io

drive = build_service('drive', 'v3', service_name='google-draas')
req = drive.files().get_media(fileId=FILE_ID)
fh = io.BytesIO()
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
with open('original.docx', 'wb') as f:
    f.write(fh.getvalue())
```

### 2. Edit with python-docx

**Line spacing:** The docDefaults in .docx XML may set spacing that you can't see in python-docx's `paragraph_format` (it shows as `None` when inherited from the style). Apply explicit formatting:

```python
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING

doc = Document('original.docx')

for i, para in enumerate(doc.paragraphs):
    pf = para.paragraph_format
    # Set single spacing with no space after
    pf.line_spacing = 1.0
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_after = Pt(0)
    pf.space_before = Pt(0)
```

**Text replacement across runs (critical pitfall):** Text in .docx files is split across multiple runs (e.g., "2" in one run, "nd" in another for superscript ordinal suffixes). You CANNOT do simple string replacement on `paragraph.text`. Instead, manipulate individual runs:

```python
p0 = doc.paragraphs[0]
# Run 1: "  {spaces}2"  → keep spaces, strip the "2"
p0.runs[1].text = p0.runs[1].text.rstrip('2')  
# Run 2: "nd" → "17th"
p0.runs[2].text = "17th"
# Run 3: " July 2026" → " August 2026"
p0.runs[3].text = " August 2026"
```

Always verify the full concatenated text after changes:
```python
full_text = ''.join(run.text for run in doc.paragraphs[0].runs)
```

### 3. Re-upload IN PLACE (preserving file ID and link)

Use `files().update()` — NOT `files().create()`. This keeps the same URL, sharing permissions, and folder location:

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload('fixed.docx', 
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)
updated = drive.files().update(fileId=FILE_ID, media_body=media).execute()
```

You can also update the file name in the same call:
```python
drive.files().update(fileId=FILE_ID, 
    media_body=media, 
    body={'name': 'New Name - 17 Aug 2026.docx'}).execute()
```

### 4. Visual Verification (render .docx → PDF → PNG → vision_analyze)

Since you can't call the Docs API on a .docx (it errors "must not be an Office file"), visually verify by:

**Step A:** Create a temp Google Doc from the .docx (Drive conversion):
```python
media2 = MediaFileUpload('fixed.docx', mimetype='...', resumable=True)
body = {'name': 'TMP_render', 'mimeType': 'application/vnd.google-apps.document'}
temp_doc = drive.files().create(body=body, media_body=media2, fields='id').execute()
temp_id = temp_doc['id']
```

**Step B:** Export the temp Google Doc as PDF:
```python
req = drive.files().export_media(fileId=temp_id, mimeType='application/pdf')
fh = io.BytesIO()
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
with open('fixed.pdf', 'wb') as f:
    f.write(fh.getvalue())
```

**Step C:** Render PDF to PNG with pdftoppm (available on Hermes VPS):
```bash
pdftoppm -png -r 200 fixed.pdf fixed_verify
```

**Step D:** vision_analyze the rendered image — ask specifically about line spacing consistency, date correctness, and formatting.

**Step E:** Clean up — delete the temp Google Doc:
```python
drive.files().delete(fileId=temp_id).execute()
```

## Pitfalls

- **.docx → Google Doc conversion can normalize spacing.** The temp Google Doc may render differently from how the .docx looks in Word or Google Docs viewer. When possible, verify against the actual .docx preview.
- **Run-level text is fragile.** Adding or removing runs changes indices. If you need to do complex text replacement, consider using `python-docx`'s `_element` XML manipulation instead.
- **Superscript ordinals.** "2nd", "3rd", "17th" — the superscript part (st, nd, rd, th) is often a separate run with `<w:vertAlign w:val="superscript"/>` in the XML. Preserve this formatting when replacing.
- **No LibreOffice on the VPS.** You cannot use `libreoffice --headless --convert-to pdf` — the workflow above (Drive export) is the only way to render .docx to PDF.
- **Space after = 160 twips by default.** A .docx created by Word often has `w:after="160"` in the docDefaults (≈8pt paragraph spacing). This is invisible in python-docx's `paragraph_format.space_after` (returns None) but is applied by the renderer. Set explicit `space_after = Pt(0)` to override.
- **Line spacing values.** `w:line="240"` = single, `w:line="360"` = 1.5, `w:line="480"` = double. The docDefaults may use `w:line="259"` (≈1.08). python-docx `WD_LINE_SPACING.SINGLE` sets it to 240.