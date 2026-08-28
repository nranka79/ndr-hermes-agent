# Document Translation via Gemini Vision + HTML Mimicry + PDF

Translate government/legal documents from Indian languages (Kannada, etc.) to English while preserving the original document's visual layout — then convert to PDF for Drive filing.

## When to use

- User sends a scanned PDF or image of an official document in an Indian language (Kannada, Hindi, Tamil, Telugu)
- The document has formal structure: letterhead, reference numbers, date headers, body paragraphs, signature block
- The user wants an English translation that preserves the original layout for easy cross-reference

## Workflow

### Step 1: Extract text via Gemini multimodal

Use Gemini 2.5 Flash via OpenRouter with the PDF/image as a direct input:

```python
from hermes_tools import terminal

# First get the image into a format OpenRouter can accept
# For PDF, render first page to JPEG
cmd = '''
python3 -c "
import fitz
doc = fitz.open('/path/to/document.pdf')
page = doc[0]
pix = page.get_pixmap(dpi=200)
pix.save('/tmp/doc_page.jpg')
doc.close()
print('done')
"
'''
terminal(cmd)
```

Then call `vision_analyze` with the rendered JPEG to extract the text and understand the layout. The Gemini model reads the Kannada text directly from the image — no separate OCR step needed.

**Prompt pattern for translation:**
> "This is a Kannada government letter. Translate the COMPLETE text into English. Preserve all reference numbers, dates, names, amounts, and legal terminology exactly. After the translation, describe the document's visual layout — margins, indentation, alignment of each section, spacing between paragraphs, positioning of the letterhead vs body vs signature."

### Step 2: Create HTML that mimics the original layout

Build an HTML page that visually mirrors the original document:

- Same margins (left margin typically wider for government letters)
- Same text alignment (left-aligned body, right-aligned signature)
- Same paragraph spacing (single/double line gaps between sections)
- Bold headers mirroring the original's emphasis
- A ruled line for the letterhead separator if present
- Same signature block positioning

**Key CSS:**
```css
@page { size: A4; margin: 2.5cm 2cm 2cm 3cm; }
body { font-family: 'Noto Serif', 'Times New Roman', serif; font-size: 11pt; line-height: 1.6; }
.header { text-align: center; margin-bottom: 20px; }
.ref-section { margin-bottom: 15px; }
.body-text { text-indent: 2em; margin-bottom: 10px; }
.signature { margin-top: 40px; text-align: right; }
```

### Step 3: Convert HTML to PDF

Two options:

**Playwright (better for layout fidelity):**
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html_content)
    page.pdf(path='/path/to/output.pdf', format='A4', margin={'top': '0mm', 'right': '0mm', 'bottom': '0mm', 'left': '0mm'})
    browser.close()
```

**WeasyPrint (lighter, no browser dependency):**
```python
from weasyprint import HTML
HTML(string=html_content).write_pdf('/path/to/output.pdf')
```

### Step 4: Rename per convention

```
YYYYMMDD_ProjectName_DocumentType_LanguageVariant.ext
```

**Examples:**
- `20260709_SerenityHillView_LandConversionCancellation_OriginalKannada.pdf`
- `20260709_SerenityHillView_LandConversionCancellation_EnglishTranslation.pdf`
- `20260709_SerenityHillView_LandConversionCancellation_EnglishTranslation.html`

### Step 5: File on Drive

1. Find the project's Drive folder (e.g. `DRA Projects > Serenity Hill View`)
2. Find/create a `Legal` subfolder
3. Upload all files there (original + translation PDF + optional HTML)
4. Generate shareable links for the English versions

## Provider Selection

| Provider | Works with | Notes |
|----------|-----------|-------|
| OpenRouter Gemini 2.5 Flash | Image URLs, Base64 data URLs | Use when you can host/encode the image to a URL. Default via `call_openrouter_model` |
| Vision Analyze | Local file paths | Use for direct OCR + layout description on local images |
| Gemini via Browser | Interactive | Fallback if OpenRouter rate-limited |

For OpenRouter multimodal with image data, encode the image as base64 data URL:
```
data:image/jpeg;base64,<base64_string>
```

## Pitfalls

- **Hallucinated text in translation:** Gemini may add explanatory text not in the original. The prompt must explicitly say "translate COMPLETE text, do not add or summarize anything."
- **Layout drift in PDF:** Different renderers (Playwright vs WeasyPrint vs browser) produce slightly different margins and pagination. Test with the actual renderer before filing.
- **Missing Unicode fonts:** Kannada/devanagari characters may not render in WeasyPrint's default fonts. Install `noto-fonts` or specify a Unicode font stack:
  ```css
  body { font-family: 'Noto Sans Kannada', 'Noto Sans', sans-serif; }
  ```
- **LLM+Code boundary:** The HTML template can be LLM-generated (it's creative/structural), but the translated text must be treated as an opaque data blob inserted into the template by code — never re-generated. See `references/llm-code-boundary-principle.md`.
- **Vision analyze vs OpenRouter approach:** `vision_analyze` is free (local OCR for readable text) but may not handle Kannada/south Indian scripts well for full translation. Gemini via OpenRouter handles Indian scripts natively. Prefer OpenRouter Gemini for Indian language documents.
