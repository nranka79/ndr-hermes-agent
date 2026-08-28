# Multi-Agent PDF Legal Judgment Analysis → Google Doc Summary

**When to use:** User asks you to analyze a large PDF judgment/court order (50+ pages, 5000+ lines), produce a detailed summary with paragraph-level citations, and save it as a Google Doc in the same Drive folder as the source PDF.

## Workflow

### Phase 1 — Download & Prepare

1. **Find the attachment** in Gmail (typically the email contains a PDF attachment)
2. **Download** it to `/tmp/` using Gmail API's `attachments().get()`
3. **Extract text** via `pdftotext` (faster than PyMuPDF for pure text PDFs):
   ```bash
   pdftotext /tmp/source.pdf /tmp/judgment_text.txt
   wc -l /tmp/judgment_text.txt  # Check size — if 5000+ lines, parallel analysis is needed
   ```
4. **Read the first 100-200 lines** to identify the case structure (parties, bench, date, case numbers, final order location)

### Phase 2 — Spawn Parallel Analysis Agents

Use `delegate_task` with 3-4 agents, each analyzing a contiguous chunk of the text file. Split by logical section boundaries (not arbitrary line counts):

| Agent | Lines | What to Extract |
|-------|-------|-----------------|
| Part 1 | ~1-1500 | Case details, parties, Single Judge order summary, appellant's specific grievance, PIL challenges, interim orders |
| Part 2 | ~1500-3500 | All contentions raised by petitioners vs State's counter-arguments, with paragraph/page numbers |
| Part 3 | ~3500-end | Division Bench's analysis per issue, final findings, final order paragraphs |

**Key instruction for every agent (MANDATORY):**
> "For every conclusion, note the exact page/paragraph/serial number from the text. Every conclusion MUST be linked to a paragraph number."

Set `toolsets: ["file"]` for each agent since they only need to read the local file.

### Phase 3 — Compile Summary & Upload Source PDF

1. **Rename the source PDF** with the standard naming convention: `YYYYMMDD_Court_Bench_Topic_CaseNumber.pdf`
2. **Upload to the correct Drive folder** (e.g., RnD → Bangalore for policy/planning judgments)
3. **Compile all agent summaries** into a structured Google Doc

### Phase 4 — Create Google Doc Summary

1. **Create a Google Doc** in the **same Drive folder** as the source PDF:
   ```python
   docs = build_service('docs', 'v1')
   doc_meta = {
       'name': f'{YYYYMMDD}_Topic_Summary_CaseNumber',
       'parents': [TARGET_FOLDER_ID],
       'mimeType': 'application/vnd.google-apps.document'
   }
   doc = drive.files().create(body=doc_meta, fields='id, name, webViewLink').execute()
   ```

2. **Structured content template:**
   ```
   ═══════════════════════════════════════════
   1. CASE OVERVIEW
   ═══════════════════════════════════════════
   Court, Bench, Date, Case Numbers, Parties, Outcome

   ═══════════════════════════════════════════
   2. THE SINGLE JUDGE/RECORD ORDER
   ═══════════════════════════════════════════
   What the lower court/single judge ruled, with key holdings

   ═══════════════════════════════════════════
   3. KEY CONTENTIONS RAISED
   ═══════════════════════════════════════════
   A. Issue 1 — Arguments [Paras XX-YY, pp. ZZ]
   B. Issue 2 — Arguments [Paras XX-YY, pp. ZZ]

   ═══════════════════════════════════════════
   4. COURT'S ANALYSIS & FINDINGS
   ═══════════════════════════════════════════
   A. Issue 1 — FINDING: [Accepted/Rejected] [Para X]
      Reasoning: ...
   B. Issue 2 — FINDING: [Accepted/Rejected] [Para Y]

   ═══════════════════════════════════════════
   5. FINAL ORDER [Paras XX-YY]
   ═══════════════════════════════════════════
   Exact holding, what was dismissed/allowed, any conditions/riders

   ═══════════════════════════════════════════
   6. PRACTICAL IMPLICATIONS
   ═══════════════════════════════════════════
   What this means operationally
   ```

3. **Every concluding statement** must end with a paragraph reference in brackets: `[Para X, pp. Y-Z]`

### Phase 5 — Deliver

1. **Send the Google Doc link** to the user via Telegram
2. **Also send the source PDF link** (already uploaded to Drive)
3. **Summarize key findings** in a few bullet points

## Pitfalls

- **PDF is scanned/image-based:** If `pdftotext` produces empty output or garbled text, use `pdftoppm` to convert pages to PNG images, then OCR with `tesseract` (English + Hindi for Indian judgments). This is slower but necessary for scanned documents.
- **Very large judgments (100+ pages):** Split into 4+ agent chunks, not 3. Each chunk should be ~1500-2000 lines. Keep each agent's analysis focused and not too broad.
- **Paragraph numbering inconsistency:** The PDF's internal paragraph numbers may skip, restart, or use a different scheme than the text extraction line numbers. Reference paragraphs by their SERIAL NUMBER (¶ 1, ¶ 2...) or the judgment's OWN paragraph numbering (e.g., "Para 164") rather than line numbers.
- **Agent summaries may contradict:** If two agents give different interpretations of the same holding, flag both and let the user decide. Do not silently pick one.
- **BatchUpdate length limits:** Google Docs API has a 1MB request limit. For very long doc content (>50KB text), split into multiple `insertText` requests or write to a local file and upload as a Docs-style file.
- **Cross-reference with single judge order:** If the appeal is against a single judge order, Part 1 of the analysis needs to reconstruct the single judge's ruling from the division bench's summary. The single judge order may not be in the same PDF — it's quoted or summarized within the division bench judgment.
