# Legal Case Master Notes — Absorbed from productivity/legal-case-master-notes

## What This Reference Covers

Compile comprehensive Master Notes from a Drive folder of legal case documents — parallel OCR agents, multi-cycle verification, structured python-docx synthesis, and Drive upload. For DRAAS legal team when studying case documents for litigation strategy.

**Skill status:** Absorbed into `legal-document-drafting` umbrella (2026-05-29). Original at `productivity/legal-case-master-notes/`.

## When to Use

"Create master notes from documents", "compile all case documents", "study every document in this folder", "comprehensive analysis of court documents"

**NOT the same as `legal-document-drafting`** — that is for transaction documents (sale deeds, PSAs). This is for litigation-preparation research.

## Workflow

### Phase 1 — Drive Folder Survey
1. List all files, classify by type: Pleadings, IAs, Affidavits, Orders, Judgments, Certificates
2. **CRITICAL:** Map filenames to legal identities — "06_Orders_IA_No2.pdf" may actually be "Orders on IA No.5 to 7 disposed together"

### Phase 2 — Parallel OCR (Multi-Agent)
- Spawn 3–6 documents per agent
- Use `anthropic/claude-sonnet-4.6` via OpenRouter directly — **NOT** `vision_analyze` (hardcoded to invalid `google/gemini-2.0-flash`)
- Save to `/tmp/extracted/batchN/doc_name.txt`

### Phase 3 — Read Key Documents First
Read MOU, Written Statement, Key Affidavit, one IA order, and HC Judgment yourself before spawning synthesis agents.

### Phase 4 — Spawn Synthesis Agents (max 3 concurrent)
- Agent 1: Executive Briefing Note (narrative summary)
- Agent 2: Chronology & Timeline
- Agent 3: Parties & Pleadings
- Agent 4: IAs, Orders & Judgments
- Agent 5: [User]'s Legal Position (always include for Nishant Ranka)

### Phase 5 — Review Cycles (minimum 2)
- Cycle 1: Completeness check
- Cycle 2: Fact verification (every date/amount/citation must have source)

### Phase 6 — python-docx Assembly & Drive Upload

## Critical Pitfalls

1. **IA number misidentification** — always read file content to confirm IA number, not filename
2. **Vision model** — use `anthropic/claude-sonnet-4.6` NOT `vision_analyze` (invalid model ID)
3. **Sub-agent PDF timeouts** — documents over 20 pages cause 600s timeouts; do in main session or split
4. **Legal research agents return US cases** — always include India-specific terms: "AIR", "SCC", "site:indiankanoon.org", "Karnataka HC", "Madras HC"
5. **Hosur = Karnataka jurisdiction** — NOT Tamil Nadu despite proximity to border
6. **Every fact must cite source** — inline citations in Master Notes are mandatory

## Nishant Ranka Position Section (always include)

- Non-signatory to all documents
- Heir of late Ganesh Ranka (NOT Dinesh Ranka's lineage — separate)
- Partnership dissolved on Dinesh's death (26 July 2023) under Section 42 IPA 1932
- Rajesh Shah's post-death acts (amended plaint filed after 26 July 2023) were unauthorized
- Right to file counter-suits against Rajesh Shah for fraud/misrepresentation

## Scripts

- `scripts/extract_legal_vision.py` — batch OCR for scanned PDFs via OpenRouter `anthropic/claude-sonnet-4.6`
