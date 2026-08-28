# Court Judgment / Legal Order Analysis (Multi-Agent Parallel)

Analyze a large court judgment PDF by splitting it into sections, analyzing each in parallel via delegate_task, then compiling a comprehensive summary with paragraph-level citations.

## Trigger

User sends a judgment/legal order PDF and asks for a detailed summary with citations.

## Workflow

```
1. Extract text from PDF          → pdftotext
2. Understand document structure   → read beginning + use grep for key sections
3. Spawn parallel analysis agents  → 3-4 agents, each covering a section
4. Compile findings                → merge agent outputs
5. Create Google Doc summary       → Drive + Docs API (structured with headers)
6. (Optional) Export as PDF        → Drive export_media
7. (Optional) Email to thread      → Gmail draft with PDF attachment
```

## Step 1 — Extract & Understand

```bash
pdftotext input.pdf /tmp/judgment.txt
wc -l /tmp/judgment.txt
```

Use `grep` to find key sections:
```bash
grep -n "order\|conclusion\|dismiss\|allowed\|finding\|.*JUDGMENT\|FINAL" /tmp/judgment.txt | head -20
```

Read the beginning (case caption, parties) and end (final order) to understand structure.

## Step 2 — Map Section Boundaries

Based on structure, split into logical sections (typically 3-4):

| Section | Content | Typical Lines |
|---------|---------|---------------|
| 1 | Case background, parties, Single Judge order, PIL details | 1-~1500 |
| 2 | Contentions and arguments, petitioner's case, pricing comparisons | ~1500-~3500 |
| 3 | Division Bench analysis, reasoning, findings, final order | ~3500-end |

Adjust boundaries based on actual document structure.

## Step 3 — Spawn Parallel Agents

```python
tasks = [
    {"goal": "Analyze sections A-C: case background, parties, single judge order",
     "context": "Read /tmp/judgment.txt lines 1-1500...",
     "toolsets": ["file"]},
    {"goal": "Analyze sections D-F: contentions and arguments",
     "context": "Read /tmp/judgment.txt lines 1500-3500...",
     "toolsets": ["file"]},
    {"goal": "Analyze sections G-I: analysis, findings, final order",
     "context": "Read /tmp/judgment.txt lines 3500-end...",
     "toolsets": ["file"]},
]
results = delegate_task(tasks=tasks)
```

**Important quality requirements to include in each agent's goal:**
- "For each point, note the page/paragraph number from the text"
- "Every conclusion MUST be linked to a paragraph number"
- Be explicit about which sections each agent should cover

## Step 4 — Compile & Create Google Doc

Create a Google Doc via Drive API + Docs API with:
- Headings for each major section (use level 1-2 headers)
- Sub-headings for each contention/finding
- Paragraph references inline: `[Para 164]` or `[Paras 78-90, pp. 71-78]`
- A final key findings table or bullet summary

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')
docs = build_service('docs', 'v1')

doc = drive.files().create(body={
    'name': 'YYYYMMDD_Subject_Summary',
    'parents': [target_folder_id],
    'mimeType': 'application/vnd.google-apps.document'
}, fields='id, name, webViewLink').execute()

# Write content in a single batchUpdate
requests = [{
    'insertText': {
        'location': {'index': 1},
        'text': full_summary_text
    }
}]
docs.documents().batchUpdate(documentId=doc['id'], body={'requests': requests}).execute()
```

## Step 5 — (Optional) Export & Email

Export as PDF and create a Gmail draft with attachment (see `gws-automation` → `references/gmail-attachment-pattern.md`).

## Pitfalls

- **Don't try to read 5000+ lines in a single read_file call** — use offset/limit or let agents read their assigned sections
- **Agent context limits** — keep each agent's section manageable (under ~2000 lines or ~100K chars)
- **Paragraph numbering varies** — judgments may use serial numbers (1, 2, 3...) or internal paragraph marks (¶). Use what's in the text
- **OCR quality** — scanned PDFs may have garbled text; page numbers may be unreliable. Fall back to line numbers if needed
