# .docx → PDF Conversion via WeasyPrint

Convert a .docx file to a clean, properly formatted PDF when **LibreOffice is unavailable**. Uses `python-docx` to extract formatting (margins, font sizes, alignment, spacing) → reconstructs as HTML with inline styles → renders with `weasyprint`.

## When to Use

- `libreoffice --headless --convert-to pdf` is not installed
- The document is a simple text document (no complex tables, images, headers/footers)
- The document uses standard fonts (Times New Roman, etc.) and basic paragraph formatting

## Full Recipe

### 1. Install dependencies (if needed)

```bash
uv pip install weasyprint pypdf
```

### 2. Extract formatting from docx + build HTML + render

```python
from docx import Document
from docx.shared import Pt, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from weasyprint import HTML

SRC = '/path/to/input.docx'
OUT = '/path/to/output.pdf'

doc = Document(SRC)
section = doc.sections[0]

# Page dimensions (EMU → mm)
page_w = section.page_width / 914400 * 25.4
page_h = section.page_height / 914400 * 25.4
lm = section.left_margin / 914400 * 25.4
rm = section.right_margin / 914400 * 25.4
tm = section.top_margin / 914400 * 25.4
bm = section.bottom_margin / 914400 * 25.4

def emu_to_pt(emu):
    return emu / 12700

def para_to_html(p):
    align_map = {
        WD_ALIGN_PARAGRAPH.LEFT: 'left',
        WD_ALIGN_PARAGRAPH.CENTER: 'center',
        WD_ALIGN_PARAGRAPH.RIGHT: 'right',
        WD_ALIGN_PARAGRAPH.JUSTIFY: 'justify',
    }
    align = align_map.get(p.alignment, 'left')
    sb = emu_to_pt(p.paragraph_format.space_before) if p.paragraph_format.space_before else 0
    sa = emu_to_pt(p.paragraph_format.space_after) if p.paragraph_format.space_after else 0

    runs_html = []
    for r in p.runs:
        text = r.text
        if not text.strip():
            continue
        fs = r.font.size.pt if r.font.size else 11
        bold = ' font-weight:bold;' if r.font.bold else ''
        italic = ' font-style:italic;' if r.font.italic else ''
        style = f'font-size:{fs}pt; font-family:"Times New Roman", Times, serif;{bold}{italic}'
        runs_html.append(f'<span style="{style}">{text}</span>')

    if not runs_html:
        if p.text.strip():
            runs_html.append(f'<span style="font-size:11pt; font-family:\'Times New Roman\', Times, serif;">{p.text}</span>')
        else:
            return f'<p style="margin:{sb}pt 0 {sa}pt 0; text-align:{align}; font-size:1pt;">&nbsp;</p>'

    return f'<p style="margin:{sb}pt 0 {sa}pt 0; text-align:{align}; line-height:1.15;">{"".join(runs_html)}</p>'


html_parts = [
    '<!DOCTYPE html><html><head><meta charset="utf-8">',
    f'<style>@page {{ size: {page_w:.2f}mm {page_h:.2f}mm; margin: {tm:.2f}mm {rm:.2f}mm {bm:.2f}mm {lm:.2f}mm; }}</style>',
    '</head><body>',
]
for p in doc.paragraphs:
    html_parts.append(para_to_html(p))
html_parts.append('</body></html>')

HTML(string='\n'.join(html_parts)).write_pdf(OUT)
```

### 3. Verify

```bash
# Page count
python3 -c "from pypdf import PdfReader; r = PdfReader('$OUT'); print(f'Pages: {len(r.pages)}')"

# Visual check (convert to PNG)
pdftoppm -png -r 200 "$OUT" /tmp/preview
# Then vision_analyze the /tmp/preview-1.png
```

## Handling Unicode Characters

If the docx contains em dashes (—), smart quotes, or other non-Latin-1 characters:

- **WeasyPrint handles Unicode natively** when the HTML includes `<meta charset="utf-8">` and the body uses a font family that supports those characters
- Times New Roman (sRGB font) supports em dashes, smart quotes, and accented Latin characters
- For CJU/Devanagari/other scripts, add a Google Fonts fallback:
  ```css
  body { font-family: "Times New Roman", "Noto Sans Devanagari", serif; }
  ```

## Comparison with Alternatives

| Method | Availability | Quality | Unicode Support |
|--------|------------|---------|----------------|
| LibreOffice (CLI) | Not installed | Excellent | Full |
| **WeasyPrint (this recipe)** | pip-installable | Good (no embedded images/tables) | Full |
| fpdf2 (direct render) | pip-installable | Poor (text wrapping, margin issues) | Needs DejaVu TTF |
| pandoc → wkhtmltopdf | Need both | Good | Full |

## Limitations

- **No table support** — python-docx tables need separate HTML `<table>` construction
- **No image support** — inline shapes aren't rendered; use a separate approach for image-heavy docs
- **No embedded charts/objects** — they're silently dropped
- **Font fallback** — weasyprint uses system fonts; verify the preview for font substitutions
- **Line spacing** — approximate via `line-height` CSS; may differ slightly from Word rendering

## Pitfall: Using fpdf2 (DON'T)

fpdf2 with the built-in Helvetica/Times core fonts cannot handle Unicode characters (em dashes, smart quotes). Even when switching to DejaVu TTF:
- Text reflow is poor (fpdf2 doesn't do word-wrap the same way Word does)
- Margins and alignment are easily lost
- The result looks visibly distorted (as verified in this session 2026-08-22)

**Always prefer WeasyPrint for docx→PDF conversion.** fpdf2 is fine for generating simple structured PDFs from scratch (like form letters or certificates) but NOT for converting an existing formatted docx.