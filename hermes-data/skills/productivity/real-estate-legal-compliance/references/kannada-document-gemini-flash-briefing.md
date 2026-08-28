# Kannada Document Analysis — vision_analyze + Gemini 2.5 Flash

Alternative to Tesseract OCR for understanding Kannada government documents (BBMP endorsements, CC applications, land records, etc.) that produces a structured professional briefing note rather than a full replica.

## When to Use

- User asks "what does this Kannada document say?" or "translate this Kannada document"
- The document is scanned (image-based, not extractable text) — typical for BBMP/KRERA/DC office correspondence
- You need a briefing note summary, NOT an exact HTML replica (see `kannada-government-letter-workflow.md` for the replica approach)
- The document has 5-15 pages of internal file notes, endorsements, or correspondence

## Workflow

### Phase 1: Download from Drive

```python
drive = build_service('drive', 'v3')
file_id = 'FILE_ID'
request = drive.files().get_media(fileId=file_id)
content = request.execute()
with open('/opt/data/LOCAL_NAME.pdf', 'wb') as f:
    f.write(content)
```

### Phase 2: Convert PDF Pages to PNG Images

```bash
mkdir -p /opt/data/document_pages
# For all pages:
pdftoppm -png -r 200 /opt/data/LOCAL_NAME.pdf /opt/data/document_pages/page_
# For specific pages:
pdftoppm -png -r 200 -f 1 -l 12 /opt/data/LOCAL_NAME.pdf /opt/data/document_pages/page_
```

**Note:** `pdftoppm` appends a suffix like `-01.png`, `-02.png` etc. So the actual filenames will be `page_01-01.png`, `page_01-02.png`, etc. Check actual filenames with `ls` before passing to vision_analyze.

### Phase 3: Analyze Pages with vision_analyze

Process 3-4 pages per batch (parallel calls). For each page, ask:

```python
vision_analyze(
    image_url="/opt/data/document_pages/page_01-01.png",
    question="This is page N of a Kannada document called [NAME]. Describe everything in detail — "
             "title, header, any numbers, stamps, seals, signatures, dates, reference numbers, "
             "department names, property details, amounts. What type of document is this?"
)
```

**Key elements to extract from each page:**
- BBMP reference numbers (e.g., `BBMP/Addl.Dir/JD NORTH/0037/2013-14`)
- Dates in DD-MM-YYYY or DD/MM/YYYY format
- Department/office names (Joint Director TP, Assistant Engineer, etc.)
- Property details (survey numbers, ward numbers, addresses)
- Financial amounts (fee amounts, DD numbers)
- Names of officials who signed
- Application or endorsement references cited
- Any conditions or decisions stated

**When Kannada OCR quality is poor:** vision_analyze often cannot read Kannada text characters accurately via OCR, but it CAN describe:
- The structure of the document (endorsement letter, internal noting sheet, court order)
- The reference numbers (English numerals survive in the scan)
- The dates
- The officials' names (when written in English or clear Kannada)
- The overall purpose and flow of the content
- Signatures and approval chains
- Any English words or abbreviations embedded in the document

This descriptive analysis is sufficient for a professional briefing.

### Phase 4: Compile Findings Into a Structured Brief via Gemini 2.5 Flash

Send a structured prompt to Gemini 2.5 Flash via `call_openrouter_model` with:
- All page-by-page findings from vision_analyze
- The document name, source URL, total pages
- A professional briefing structure template

```python
call_openrouter_model(
    user_trigger_phrase="use openrouter to analyze Kannada documents with Gemini 2.5 Flash",
    model="google/gemini-2.5-flash",
    max_tokens=4000,
    prompt=f"""You are a legal document analyst. Compile a comprehensive BRIEFING NOTE based on the following document analysis.

DOCUMENT: [NAME]
SOURCE: [DRIVE LINK]

[ALL PAGE FINDINGS FROM VISION_ANALYZE]

Please create a PROFESSIONAL BRIEFING NOTE in this format:

# BRIEFING NOTE
## Document: [NAME]

**Analysis Method:** Translated from Kannada using Gemini 2.5 Flash

**Document Type:** [BBMP Internal Note / Endorsement / CC / Order / Letter]

**Total Pages:** N

**Ref No:** [PRIMARY REFERENCE NUMBER]

**Date Range:** [EARLIEST DATE] to [LATEST DATE]

1. Document Overview
2. Key Contents (by page/section)
3. Property Details
4. Key Decisions & Recommendations
5. Approval Chain (who signed, dates)
6. Notable Points
7. Relationship to Other Documents

---
*Document analyzed using Google Gemini 2.5 Flash via OpenRouter.*
"""
)
```

### Phase 5: Save Briefing Note

Save the briefing note with a clear naming convention:

```
/opt/data/[Project]_BriefingNote_[DocDescription]_Gemini25Flash.md
```

Example: `Ranka_Iris_BriefingNote_ReSanctionSWD_BBMP_MiscDocs_Gemini25Flash.md`

### Phase 6: Present to User

Deliver key findings in a structured Telegram message:
- What type of document it is
- Key reference numbers and dates
- Key decisions found
- Notable findings (delays, fee amounts, approval chains)
- The file location of the full briefing note

## Differences from Tesseract OCR Approach

| Approach | Tesseract OCR (`kannada-government-letter-workflow.md`) | vision + Gemini Flash (this reference) |
|----------|--------------------------------------------------------|----------------------------------------|
| **Goal** | Produce an exact HTML replica with same layout | Produce a professional English briefing note |
| **Accuracy needed** | High — must match original content/layout exactly | Medium — key facts, dates, decisions, flow |
| **Best for** | Official replies, notices that need response | Internal file notes, long compilations, noting sheets |
| **Kannada text handling** | Tesseract with Kannada language pack | vision_analyze descriptive + Gemini synthesis |
| **Output** | HTML file → upload to Drive | Markdown file → store locally / present in chat |

## Known Limitations

- **vision_analyze cannot reliably OCR Kannada text characters.** It CAN read:
  - English numerals and dates ✓
  - English abbreviations (DD, JD, Addl, LP, CC, OC, NOC, etc.) ✓
  - Document structure and layout ✓
  - Stamp/seal/signature positions ✓
  - Handwritten dates and initials ✓
  - **NOT** flowing Kannada script paragraphs ✗
- **Gemini 2.5 Flash provides the translation/synthesis** — it synthesizes the findings from vision_analyze into coherent English narrative
- **Not suitable for exact translation** — use the Tesseract + Kannada OCR approach for word-for-word accuracy
- **OpenRouter credit limits** — large documents (12+ pages) may need to be summarized per-page before sending to Gemini
