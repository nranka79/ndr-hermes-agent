---
name: knowledge-base-audit
description: "Audit a knowledge base document against source material (briefings, FAQ lists, training data), identify gaps/outdated content, and produce a companion doc with yellow-highlighted updates and source citations — without touching the original."
version: 1.0
author: Hermes Agent
tags: [Knowledge-Base, Gap-Analysis, Documentation, Google-Docs, Companion-Doc]
related_skills: [google-doc-formatting-template, google-workspace]
---

# Knowledge Base Audit & Companion Document

Class-level skill for auditing a knowledge base document (Google Doc) against new source material — briefings, FAQ training data, interview transcripts — and producing a companion document that preserves the original while showing what's been updated.

## Trigger

- "Audit this KB doc against the Joyce AI FAQ data"
- "What's missing from this document vs what we need?"
- "Create a companion doc with updates, don't touch the original"
- "Highlight all changes in yellow and cite the source"
- "I want you to understand what we are missing in this overall project facts"
- Any request involving KB review, gap identification, or annotated companion creation

## Workflow

### Phase 1: Read the Original Document

1. **Download the source doc** — export as `.docx` via `export?format=docx` or read via txt export
2. **Extract full text** — use pyunzip + xml.etree for docx, or vision_analyze for scanned content
3. **Understand the document structure** — identify:
   - Q&A format vs narrative sections
   - Which questions/answers are factual (project specs) vs opinion/objection handling vs pricing/finance
   - Any sections that defer answers to other documents

### Phase 2: Identify Gaps Against Source Material

Compare the KB against the new source material (NDR briefings, Joyce AI FAQ questions, training data). Look for:

| Gap Type | Example Signal |
|----------|---------------|
| **Outdated info** | KB says "G+1/G+2/G+3 subject to Panchayat norms" but NDR briefing says "G+4 per TN BTCP norms" |
| **Missing answer** | NDR gave bus stop details but KB says "does not provide exact distance" |
| **Missing topic** | Joyce AI has a rental-yield question, KB has nothing on it |
| **Weak position** | KB says "6 months cannot be committed" but NDR now says it CAN |
| **Missing tone directive** | NDR's PEPPY/high-energy framing is absent from KB |
| **Missing investment thesis** | NDR's "Economics 101" supply-demand story isn't in the KB |

**Critical: Check for CONTRADICTIONS** — where KB says one thing and source says another. These are the highest-priority updates.

### Phase 3: Create Companion Document (Preserve Original)

**NEVER modify the original document.** Always create a new companion doc.

1. **Create a new Google Doc** — use `docs_service.documents().create()` with a descriptive title:
   `"{Project Name} — Updated KB (v2 — With Corrections & Sources)"`

2. **Insert full original content** — use `insertText` at index 1. This preserves the entire original text as the base.

3. **Tag each update** — for every gap/outdated item, insert an update block immediately after the relevant original paragraph, formatted as:

   ```
   [UPDATE — Date Source Person] The update description...
   Source: Person, Date — Briefing Name
   ```

4. **Yellow-highlight ALL new content** — use Docs API `updateTextStyle` with `backgroundColor`:

   ```python
   requests = []
   for update_start, update_end in update_blocks:
       requests.append({
           "updateTextStyle": {
               "range": {
                   "startIndex": 1 + update_start,  # Docs API is 1-indexed
                   "endIndex": 1 + update_end
               },
               "textStyle": {
                   "backgroundColor": {
                       "color": {
                           "rgbColor": {"red": 1.0, "green": 1.0, "blue": 0.0}
                       }
                   }
               },
               "fields": "backgroundColor"
           }
       })
   ```

5. **Add a prominent note at the top** — also yellow-highlighted:
   ```
   IMPORTANT NOTE: This document contains ALL content from the original KB document, plus updates and corrections based on [source]. Every addition or correction is highlighted in YELLOW and includes its source reference.
   ```

### Phase 4: Source Every Update

Every update block MUST end with a clear source citation:

```
Source: NDR, 16 August 2026 — Building Height Briefing
Source: NDR, 16 August 2026 — Connectivity Briefing
Source: NDR, 16 August 2026 — Investment Thesis & Rental Yield Briefing
```

Use a consistent format: `Source: [Person], [Date] — [Briefing Name]`

This allows the reader to trace every update back to the original briefing.

### Phase 5: Track What You Updated

Present a clear summary table to the user:

| # | Update | Covers |
|---|--------|--------|
| 1 | Developer identity | Ranka Group 5-decade legacy + rebranding |
| 2 | Building height | G+4 per TN BTCP norms |
| ... | ... | ... |

Group into categories: Facts corrected, Missing answers filled, New sections added, Tone/strategy directives.

## Yellow Highlighting via Docs API — Technical Reference

The Google Docs API `backgroundColor` field uses `rgbColor` with float values (0.0–1.0), not hex:

```python
# Yellow highlight
"backgroundColor": {
    "color": {
        "rgbColor": {"red": 1.0, "green": 1.0, "blue": 0.0}
    }
}
```

**Critical: Use correct indices.** The Docs API is 1-indexed (index 1 = first character after the document title). When you find character positions in the extracted text (0-indexed), add 1:
- `doc_start_index = 1 + flat_text_position`
- `doc_end_index = 1 + flat_text_end`

**Batch limit:** Docs API accepts max ~5 `updateTextStyle` requests per batchUpdate call. Batch in groups of 5.

**Finding update positions:** After inserting all text, read the document content and find the `[UPDATE` markers by scanning the full text:

```python
import re
full_text = ""
for elem in content:
    para = elem.get('paragraph')
    if para:
        for run in para.get('elements', []):
            tr = run.get('textRun')
            if tr and tr.get('content'):
                full_text += tr['content']

update_blocks = []
for match in re.finditer(r'\[UPDATE', full_text):
    update_start = match.start()
    # Find next "Source: " after this UPDATE
    source_match = re.search(r'Source: [^\n]*', full_text[update_start:])
    if source_match:
        block_end = update_start + source_match.end()
        update_blocks.append((update_start, block_end))
```

## Document Structure Template

Use this format for the companion doc:

```
Ranka Udaya — Updated Project Facts and FAQs (v2 — With Corrections & Sources)

IMPORTANT NOTE: [yellow-highlighted] This document contains ALL content from the original KB document, plus updates and corrections based on [source]. Every addition or correction is highlighted in YELLOW and includes its source reference.

================================================================================
SECTION HEADER (original content preserved)
================================================================================

What is Ranka Udaya?
[original answer preserved exactly]

[UPDATE — 16 Aug 2026 NDR Briefing] The update description...
Source: NDR, 16 August 2026 — Briefing Name

... rest of section with all original content ...

================================================================================
ADDITIONAL UPDATES — NEW SECTION
================================================================================

[NEW SECTION — only in companion, not in original]

Source: NDR, 16 August 2026 — Briefing Name

================================================================================
END OF DOCUMENT
================================================================================
```

## Pitfalls

- **Never touch the original.** The user will tell you explicitly: "done touch whatever the document I have shared with you, no changes, no edits, nothing." Create a NEW document.
- **Google Docs indexing is 1-based.** After `insertText`, the first character is at index 1. All subsequent `updateTextStyle` indices must be `1 + text_position_in_extracted_text`.
- **Yellow = `rgbColor(1.0, 1.0, 0.0)`.** Not `(0.9, 0.9, 0.0)` or hex `#FFFF00`. Use the exact float values for pure yellow.
- **Don't re-read indices between batches.** If you re-read the document after inserting text, the content structure may differ from what you expect (whitespace handling). Build all text-based indices from your extracted flat text, then map them with +1 offset.
- **BatchUpdate limit.** Google Docs API allows at most 5 text-style changes per call. Batch your requests in groups of 5.
- **The source citation itself should be part of the highlighted block** — the entire [UPDATE ... Source: ...] paragraph, not just the description.
- **Also highlight the IMPORTANT NOTE at the top** — it's the first thing the user sees and explains the document structure.
- **NEW SECTIONS at the bottom** (tone directives, investment theses that don't correspond to any original paragraph) should also be highlighted in full.
- **User wants VERIFIABLE updates** — they specifically asked for "a link of a document reference" so the source is traceable. Every update must cite where it came from.