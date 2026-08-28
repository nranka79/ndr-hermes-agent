# Markdown → .docx (Word) → Drive Upload

Convert a Google-Drive-stored Markdown file into a proper Word document (.docx) and upload it to Drive.

## When to Use

- User has a `.md` file on Drive (Letter of Understanding, draft agreement, briefing note) and asks for it as a Word document
- You need a format others can open in Word without markdown-renderer plugins

## Full Workflow

### 1. Download .md from Drive

```python
from tools.gws_auth import build_service

service = build_service('drive', 'v3', service_name='google-draas')
content = service.files().export(fileId=FILE_ID, mimeType='text/plain').execute()
text = content.decode('utf-8-sig')    # auto-strips BOM
```

### 2. Build .docx with python-docx

| Markdown | python-docx |
|---|---|
| `# HEADING` | `doc.add_heading(text, level=0)` |
| `## HEADING` | `doc.add_heading(text, level=1)` |
| `**Bold**` | `run.bold = True` |
| `* Bullet` / `- Bullet` | `doc.add_paragraph(text, style='List Bullet')` |
| `Between:` / `And:` labels | Bold paragraph |
| `___` | Skip — let spacing create separation |

```python
from docx import Document
from docx.shared import Pt

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

lines = text.split('\n')
for line in lines:
    s = line.strip()
    if not s: continue
    if s.startswith('# '):
        doc.add_heading(s[2:].strip(), level=0)
    elif s.startswith('* ') or s.startswith('- '):
        doc.add_paragraph(s[2:].strip(), style='List Bullet')
    elif s.startswith('**') and s.endswith('**'):
        p = doc.add_paragraph()
        p.add_run(s.strip('*')).bold = True
    elif s.startswith(('Between:', 'And:')):
        p = doc.add_paragraph()
        p.add_run(s).bold = True
    else:
        doc.add_paragraph(s)
doc.save('/tmp/out.docx')
```

### 3. Upload to Drive

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(
    '/tmp/out.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
)
result = service.files().create(
    body={'name': 'YYYYMMDD_Entity_Description.docx'},
    media_body=media,
    fields='id,name,webViewLink'
).execute()
```

## Pitfalls

- **BOM** — decode with `utf-8-sig` or `lstrip('\ufeff')`
- **python-docx not installed** — `uv pip install python-docx` (Hermes venv only; system Python is PEP 668)
- **Unicode bullets** — placeholder `●` chars pass through; leave them as intentional
- **Horizontal rules** — no native element; skip them