# Multi-Agent Legal Judgment Analysis (Parallel)

Analyze a large legal judgment (PDF) by splitting it across multiple delegate_task agents and compiling results into a structured Google Doc.

## Trigger

User shares or references a High Court / Supreme Court judgment and asks for a detailed summary with paragraph-level citations.

## Workflow

### Phase 1: Extract Text from PDF

```bash
pdftotext /path/to/judgment.pdf /tmp/judgment_analysis.txt
wc -l /tmp/judgment_analysis.txt
```

Check if text was extracted successfully. If the PDF is scanned/image-based, install `pdf2image` or `pymupdf` and convert pages to images first, then use OCR.

### Phase 2: Spawn Parallel Analysis Agents

Split the text file into roughly equal sections (e.g., 3 sections of ~1900 lines for a 5700-line document). Assign each section to a `delegate_task` agent with a specific focus:

| Agent | Lines | Focus |
|-------|-------|-------|
| Part 1 | 1–1500 | Case details, parties, Single Judge order summary, contentions raised |
| Part 2 | 1501–3500 | Arguments & counter-arguments, key legal questions |
| Part 3 | 3501–end | Division Bench analysis, constitutional findings, final order |

**Agent prompt template (customize per section):**

```
Read /tmp/judgment_analysis.txt lines [START]-[END]. Extract:
1. [Section-specific questions]
For each finding, note the exact paragraph/serial number from the text.
```

**Key requirements in every agent prompt:**
- "Note the exact page/paragraph number from the text" — this is CRITICAL for citation traceability
- Be specific about what to extract (don't ask for "summary" — ask for structured data)
- Set `toolsets: ["file"]` since agents only need to read files

### Phase 3: Compile Results

Each agent returns a structured analysis. Compile them into a single Google Doc:

1. Read the agent summaries (they're returned as tool results)
2. Organize into sections: Background → Single Judge Order → Contentions → Analysis → Final Order → Practical Implications
3. Create a Google Doc via Drive API
4. Write content via Docs API `batchUpdate`
5. Each conclusion MUST include the paragraph/page reference, e.g.: `[Para 79, pp. 71-72]`

### Phase 4: Summarize in Email + Attach PDF

1. Export the Google Doc as PDF via `drive.files().export_media()`
2. Create a Reply-All Gmail draft with:
   - Short summary in email body (key findings in scannable table format)
   - PDF attached
3. Follow `references/docs-api-create-export-attach.md` for the technical pattern

### Session Example (Jun 2026)

- **Document:** WA 1983/2025 (Karnataka HC Premium FAR Division Bench judgment)
- **Size:** 5712 lines, 194KB PDF
- **Method:**
  1. `pdftotext` extracted 5712 lines
  2. 3 parallel agents analyzed sections (lines 1-1500, 1500-3500, 3500-5712)
  3. Compiled into Google Doc with 6 sections: Case Overview → Single Judge Order → Contentions → Analysis → Final Order → Practical Implications
  4. Every conclusion linked to paragraph number
  5. Google Doc exported as PDF (93KB) and attached to Reply-All email

### Pitfalls

- **PDF is image-based:** `pdftotext` returns 0 lines. Use `pdftoppm` to convert to PNG, then OCR via vision_analyze or install OCR tools.
- **Agent hallucinates citations:** Always require "exact paragraph number" in the agent prompt. Do NOT accept summaries without source references.
- **Document too long for single agent:** Split at natural section boundaries (look for section headers like "Section (B)", "Analysis", "ORDER" in the text).
- **Google Doc write limits:** For very long documents, batchUpdate may timeout. Split into multiple smaller insertText requests.
- **Email threading across accounts:** If the original thread is in a different Gmail account, you cannot set threadId. Compose as fresh email with RE: subject and explain to user.
