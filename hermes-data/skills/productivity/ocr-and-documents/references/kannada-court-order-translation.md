# Kannada Court Order → English HTML Translation

Verified 2026-08-21 on a 2-page Sub-Divisional Officer's judgment
(Case No. ಸಂ.ಆರ್.ಎ.(ಬಿ).191/2022, Bengaluru North Sub-Division)
involving Survey No. 2/2, Pattandur Agrahara Village, K.R. Puram Hobli.

**Updated 2026-08-27** — model fix and direct-API addition from a 2-page
Assistant Commissioner order (No. AC(Ane)(K): 153/2022, dated 21/03/2023)
concerning Byadarahalli Sy.No.209/1-4, Puttappa Devasthana vs encroachers,
Smt. Manjula. Key changes below.

## Document type distinction

A **court order / quasi-judicial proceeding** (Under Karnataka Land Revenue Act
1964, Section 136(2)) has a different structure from a GPA or deed:

| Element | Court Order | GPA / Deed |
|---------|-------------|------------|
| Header | Govt emblem + Court name + Case No. | "This Deed of X is made…" |
| Officer | Presiding Officer name + designation | Notary / Registrar |
| Parties | Petitioner(s) vs Respondent(s) | Grantor(s) vs Grantee(s) |
| Body | Facts → Inquiry → Findings → Order | Recitals → Clauses → Covenants |
| Subject | Specific legal issue (e.g. RTC discrepancy) | Property transfer / authority grant |
| Conclusion | "Appeal partially allowed / remanded / dismissed" | Signatures + witnesses |

## When to use vision_analyze (NOT tesseract) for Kannada

**Existing Kannada-translation-pipeline.md says vision_analyze garbles Kannada**
— that is correct for **dense multi-page** (13+ pages) GPA/deed text. However,
**vision_analyze IS the right choice for short (1-2 page) structured legal
documents** when you prompt it to READ visually and describe, not just OCR:

- 2-page court order: `vision_analyze` with `question="Read this Kannada
  document visually — extract every word. What does it say?"` returned clean
  readable Kannada + accurate English description.
- 13-page GPA: same approach returned garbled mojibake. Tesseract `-l kan`
  was correct there.

**Rule of thumb:**
- ≤3 pages, structured layout (court order, TSIR, certificate) → `vision_analyze`
  with specific Kannada-reading prompt
- ≥4 pages, dense body text (GPA, sale deed, partition deed) → tesseract `-l kan`

## Full pipeline: Kannada court order → HTML → PDF → Drive (method B, 2026-08-27)

When using Approach B (direct OpenRouter API), the output is a complete
structured translation already written in English (with Kannada original
interspersed). The full pipeline from raw PDF to filed Drive document:

1. **Render pages to PNG** at 200–300 DPI
   ```bash
   pdftoppm -png -r 300 input.pdf /tmp/pages/page
   ```

2. **Translate via OpenRouter** — send BOTH pages in one call (Approach B above).
   The model returns Kannada original + English translation in a structured format.

3. **Build HTML with both Kannada original and English translation** — follow the
   HTML/CSS conventions below (court-order-specific). Include:
   - Government header + case number bar
   - Presiding officer
   - Body sections: Proposal → Findings → Order → Subject → Signature
   - **Both Kannada original (in Kannada Unicode, `<div class="kannada-block">`)
     and English translation** side-by-section, NOT separate documents
   - Note at bottom stating what the document is

4. **Convert to PDF via WeasyPrint** (simpler than Playwright for 2-page docs):
   ```bash
   # Install once:
   uv pip install --python /opt/hermes/.venv/bin/python weasyprint
   
   # Render:
   python3 -m weasyprint input.html output.pdf
   ```
   This produces a clean A4 PDF. WeasyPrint handles CSS @page, fonts, and
   borders correctly for legal documents. No Chrome dependency needed.

5. **Name using NDR's convention:** `YYYYMMDD_Entity_Description.pdf`
   - Original: `20230321_Byadarahalli_Sy209_AC_Order_Manjula_Kannada.pdf`
   - Translation: `20230321_Byadarahalli_Sy209_AC_Order_Manjula_English.pdf`
   (Always underscores, no spaces/dashes/parentheses in filename)

6. **Upload to correct Drive folder** — use `build_service('drive', 'v3')`
   with `MediaFileUpload`:
   ```python
   from googleapiclient.http import MediaFileUpload
   media = MediaFileUpload(local_path, mimetype='application/pdf', resumable=True)
   uploaded = drive.files().create(body={
       'name': filename,
       'parents': [folder_id]
   }, media_body=media, fields='id, webViewLink').execute()
   ```
   
   **Byadarahalli folder ID:** `1Ygoi7oeDxvZDarAsqmMS9770S0IWbPee`
   (Byadarahalli Legal files folder under the DRAAS legal structure).
   For other project areas, search the project's legal folder first.

7. **Report back** — provide links to both files (original + translation)
   plus a crisp summary of what the order says: parties, subject land,
   survey numbers, date, and the operative order (what was decided).

## Pitfalls (corrected 2026-08-27)

- **Vision model: `google/gemini-2.0-flash` is NOT a valid model ID** on this
  OpenRouter account (returns 400). Use `google/gemini-2.5-flash` instead.
  Confirmed 2026-08-27 — the user also explicitly asked for "Gemini 2.5 Flash".

```
┌─ Government Header
├─ Case Reference (Number + Date)
├─ Presiding Officer
├─ Parties (Petitioner / Vs / Respondent)
├─ Subject (dispute / issue)
├─ Reference (source letter/document)
├─ Body (Facts → Inquiry → Evidence)
├─ Order (numbered directions)     ← critical section
└─ Pronouncement (date + open court)
```

### Order section styling

The ORDER is the most important part — it states what was decided. Present it
prominently:

- **Result**: "Appeal partially allowed. Case remanded to Tahsildar."
- **Direction 1**: Review original documents
- **Direction 2**: Record extent to eligible holder (or 0-04G to original holder)
- **Direction 3**: If land acquired by any authority — obtain docs, proceed

Use an `<ol>` (numbered list) for the directions in the English translation.

## HTML/CSS styling conventions

Reuse the legal-document scaffold from `kannada-translation-pipeline.md` but with
court-order-specific adjustments:

- **Header:** `Government of Karnataka` + court name in a centered block,
  not a deed title. Use the Kannada emblem symbol ☸ (U+2638) as placeholder.
- **Parties table:** Use a `<table class="parties-table">` with label-cell column
  and vs-row, NOT the deed-style "BY AND BETWEEN" text.
- **Subject/Reference box:** Background `#f8f7f4`, left border `#8b4513` brown
  (court/legal accent). Contain Subject and Reference labels in one box.
- **Kannada original block:** `<div class="kannada-original">` with
  `font-family: 'Noto Sans Kannada'` fallback — render the ACTUAL Kannada text
  from the document IN Kannada Unicode, not transliteration.
- **English translation block:** `<div class="translation">` with left border
  `#2c5f2d` green — distinguishes translation from original.
- **Order section:** Double borders (top + bottom) to set it apart as the
  holding. Use uppercase label "ORDER" / "ಆದೇಶ".
- **Pronouncement:** Italic, smaller font (`14px`), gray (`#555`).
- **Signature:** Right-aligned, officer name + designation below a spaced
  signature line.
- **Fonts:** `EB Garamond` (serif, for body English), `Noto Sans Kannada` (for
  Kannada blocks). Import both via Google Fonts `@import` in the CSS `<style>`.

## Vision model: Google Gemini 2.5 Flash via OpenRouter (corrected 2026-08-27)

**`google/gemini-2.0-flash` returns `400 "not a valid model ID"` on this
account** — confirmed 2026-08-27, the model slug is no longer accepted.
Use **`google/gemini-2.5-flash`** instead. The user explicitly requested
"Google Gemini Flash 2.5" for this workflow.

There are two approaches to call it:

### Approach A: vision_analyze tool (preferred for single pages)

`vision_analyze(image_url=page.png, question="Read this Kannada court order
visually...")` — the tool itself routes to the configured vision model.
Works when you have individual page images and the tool is registered.

### Approach B: Direct OpenRouter API (for batch/automated translation)

When `vision_analyze` isn't registered or you need multi-image + guided
translation in a single call, POST directly to OpenRouter with base64-encoded
images. Verified 2026-08-27 on a 2-page Byadarahalli AC Order:

```python
import base64, requests

with open('page-1.png', 'rb') as f:
    img1 = base64.b64encode(f.read()).decode()
with open('page-2.png', 'rb') as f:
    img2 = base64.b64encode(f.read()).decode()

api_key = open('/data/hermes/.env').read().split('OPENROUTER_API_KEY=')[1].split('\n')[0].strip("'\"")

payload = {
    "model": "google/gemini-2.5-flash",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Translate this Kannada court order to English..."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img1}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img2}"}}
        ]
    }],
    "max_tokens": 8192
}
resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json=payload, timeout=120
)
```

**Result:** Single API call returned complete bilingual translation with all
Kannada original text + English translation, structured by document sections
(Proposal, Findings, Order, Subject). ~5275 chars, ~19s latency.
- **Date formats in Karnataka orders:** The date field in the printed header
  block (`09-05-2003`) is a **template artifact** from a decades-old form — NOT
  the real date. Real date = pronouncement clause at the end
  ("Pronounced on 29/09/2022") or the signature date block
  ("Date: 21/03/2023"). Always filter out the template-artifact dates.
- **Parties may be government officials:** The "petitioner" here was the
  **Special Tahsildar** (a government revenue officer), not a private party.
  Translate the official designation accurately: "ವಿಶೇಷ ತಹಶೀಲ್ದಾರ್" = "Special
  Tahsildar"; "ಬೆಂಗಳೂರು ಪೂರ್ವ ತಾಲ್ಲೂಕು" = "Bengaluru East Taluk".
- **OCR garbled Kannada from vision:** If the first vision_analyze call returns
  garbled Kannada (mojibake/script noise), retry with a more specific prompt:
  "Look at this image carefully. It is a Kannada language court order. READ
  IT VISUALLY and describe EXACTLY what each section says — don't OCR, read the
  image." This consistently returns clean output on structured pages.
- **The Kannada original in the HTML MUST be actual Kannada Unicode**, not
  transliterated roman text. Extract from the vision_analyze description
  (it provides the actual Kannada words in its analysis even when the raw OCR
  line is garbled — the visual description faithfully reproduces Kannada text).

## Example: Case No. ಸಂ.ಆರ್.ಎ.(ಬಿ).191/2022

Refer to `judgement_translation.html` delivered 2026-08-21 for the full styled
output pattern (2 pages → clean HTML with Kannada original + English translation
side-by-section, order prominently displayed).