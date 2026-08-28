# Generating .docx Files with python-docx

Used for legal letters, notices, memos, and acknowledgment receipts that Prakash/Nishant want as downloadable Word files.

## Setup

python-docx is pre-installed in the Hermes venv at `/opt/hermes/.venv/`. Import via the write-file → execute pattern:

```python
# write_file the script to /tmp/, then run it
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
# ... build document ...
doc.save('/path/to/output.docx')
```

## Key Patterns

### Page setup
```python
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.18)   # 1.25 inch
    section.right_margin = Cm(3.18)
```

### Font
```python
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(12)
```

### Adding paragraphs with bold/alignment
```python
p = doc.add_paragraph()
run = p.add_run('Subject: Request for Withdrawal')
run.bold = True
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p.paragraph_format.line_spacing = 1.5
p.space_after = Pt(6)
```

### Structure for legal letters
- Date (left-aligned)
- "To," block with addresses (separate paragraphs, no bullets)
- "From:" block
- Subject line (bold)
- Salutation ("Dear Sir,")
- Numbered body paragraphs (1., 1.1, etc.)
- Closing ("Yours faithfully,")
- Signature block (underscore line + name + designation)
- Acceptance/endorsement block at bottom

### File delivery
Save to `/opt/data/` and deliver via `MEDIA:/path/to/file` in the response text. The Telegram platform delivers it as a native file attachment.

## Naming convention
Use `YYYYMMDD_Entity_DocType_Description.docx` per DRAAS conventions.

## Pitfalls
- **Run the script with `chmod +x`** — Python files written via `write_file` are not executable by default.
- **Use `/opt/hermes/.venv/bin/python`** shebang, not system python3. The system python may not have python-docx installed.
- **Don't mix bold with non-bold in the same paragraph run** — use separate `add_run()` calls for mixed formatting.
- **`WD_ALIGN_PARAGRAPH.JUSTIFY` for body text** makes letters look professional.
