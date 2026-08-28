---
name: document-comparison
description: "Compare two versions of a document (docx, pdf, or plain text) and highlight substantive changes. Covers fetching both versions from Gmail attachments, extracting text, paragraph-level diffing, and presenting a structured comparison."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Documents, Comparison, Diff, Contracts, Lease, Agreements, Legal]
    related_skills: [google-workspace, ocr-and-documents]
---

# Document Comparison

Compare two document versions and extract meaningful changes. Optimised for **legal documents** (lease deeds, contracts, agreements) where changes are substantive and the user needs a clear summary, not a line-by-line diff dump.

## Trigger

- "Compare the changes between version A and version B"
- "What did they change in the draft they sent back?"
- "Show me the differences between our latest version and their response"
- Any request involving "changes", "modifications", "revisions", "redline", "diff" between two documents

## Workflow

### Phase 1: Retrieve both documents

**From Gmail attachments** (most common for contract negotiation back-and-forth):

1. Search the thread for the relevant emails — the user's "sent" version and the counterparty's reply
2. Get the **full message** (not just metadata) to access attachment IDs
3. Download each attachment via `users().messages().attachments().get()` — decode from base64 and save locally

```python
from tools.gws_auth import build_service
import base64

gmail = build_service('gmail', 'v1', service_name='google-draas')

# Get attachment from a message
msg = gmail.users().messages().get(userId='me', id=MESSAGE_ID, format='full').execute()

def find_attachments(part):
    """Recursively find all attachments in a message payload."""
    result = []
    if 'parts' in part:
        for sub in part['parts']:
            result.extend(find_attachments(sub))
    if part.get('filename') and part.get('body', {}).get('attachmentId'):
        result.append(part)
    return result

for att in find_attachments(msg['payload']):
    data = gmail.users().messages().attachments().get(
        userId='me', messageId=MESSAGE_ID, id=att['body']['attachmentId']
    ).execute()
    raw = base64.urlsafe_b64decode(data['data'])
    with open('/tmp/filename.docx', 'wb') as f:
        f.write(raw)
```

**From Google Drive**: use `drive.files().get(fileId=...).execute()` and `drive.files().export(fileId=..., mimeType='text/plain').execute()` for Google-native formats. For binary files (docx, pdf), use `drive.files().get_media(fileId=...).execute()`.

### Phase 2: Extract text from each document

**For .docx files** (most common for lease agreements):

```bash
uv pip install python-docx
```

```python
from docx import Document

doc = Document('/tmp/file.docx')
paragraphs = [(i, p.text) for i, p in enumerate(doc.paragraphs) if p.text.strip()]

# Tables are important for legal docs (rent schedules, property descriptions)
tables = {}
for ti, table in enumerate(doc.tables):
    for ri, row in enumerate(table.rows):
        cells = [cell.text.strip() for cell in row.cells]
        tables[f'T{ti}R{ri}'] = ' | '.join(c for c in cells if c)
```

#### Phase 2A: Extract run-level formatting for coloured-text changes

Counterparties often make changes in **coloured font** (e.g. red text) instead of using proper track changes. python-docx does not expose run-level formatting reliably — parse the raw DOCX XML instead:

```python
import zipfile
from xml.etree import ElementTree as ET

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

with zipfile.ZipFile('/tmp/file.docx', 'r') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)
        root = tree.getroot()

paras = []
for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    full_text_parts = []
    run_details = []  # track per-run colour info
    
    for r in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
        is_red = False
        for rPr in r.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr'):
            for color in rPr.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color'):
                if color.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '').lower() in ('ff0000', 'red'):
                    is_red = True
        
        for t in r.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t.text:
                full_text_parts.append(t.text)
                run_details.append({'text': t.text, 'is_red': is_red})
    
    full_text = ''.join(full_text_parts)
    paras.append({'text': full_text, 'runs': run_details, 'has_red': any(r['is_red'] for r in run_details)})
```

This returns structured paragraphs with a `has_red` flag — use it to highlight which paragraphs the counterparty actually touched vs. paragraphs that changed due to cascading edits.

**For .pdf files**: use `ocr-and-documents` skill (pymupdf for text-based, marker-pdf for scanned).

### Phase 3: Compare with difflib

Use `difflib.SequenceMatcher` for paragraph-level comparison — this naturally groups changes at the clause level:

```python
import difflib

our_texts = [t for _, t in our_paras]
their_texts = [t for _, t in their_paras]

matcher = difflib.SequenceMatcher(None, our_texts, their_texts)

for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag == 'equal':
        continue
    elif tag == 'replace':
        for idx in range(max(i2-i1, j2-j1)):
            o_idx = i1 + idx
            t_idx = j1 + idx
            # Show both versions side by side
    elif tag == 'delete':
        # Clause present in our version, removed in theirs
    elif tag == 'insert':
        # New clause added by them
```

### Phase 4: Classify and present changes

Group changes by significance:

| Category | Meaning |
|----------|---------|
| 🔴 **Financial** | Amounts, deposits, rent, penalties, escalations |
| 🟡 **Obligation-shifting** | Who bears cost, risk, or responsibility |
| 🟢 **Non-substantive** | PAN fill-ins, grammar, formatting, names |

Present as a structured summary — lead with the financial and obligation changes, then list minor corrections. Reference clause numbers.

#### Phase 4A: Generate HTML comparison table

For lease-deed / contract comparisons, generate a **standalone HTML file** the user can open in a browser. This scales better than long text messages for 40+ changes:

```python
html_parts = []
html_parts.append('''<!DOCTYPE html><html><head>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 40px auto; padding: 20px; background: #f5f5f5; }
  table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; }
  th { background: #333; color: #fff; padding: 10px; text-align: left; font-size: 12px; text-transform: uppercase; }
  td { padding: 10px; border-bottom: 1px solid #ddd; vertical-align: top; }
  .our { background: #e8f5e9; }
  .akbar { background: #fff3e0; }
  .red { color: #d32f2f; font-weight: bold; }
  .badge-critical { background: #f44336; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
  .badge-commercial { background: #ff9800; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
  .badge-accept { background: #4caf50; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
</style></head><body>
<h1>Lease Comparison</h1>
''')

# Group changes by category
# Category A: Cosmetic (auto-accept)
# Category B: Commercial (needs review)
# Category C: Critical (reject/negotiate)

for change in commercial_changes:
    html_parts.append(f'''<tr>
    <td>{change['clause']}</td>
    <td class="our"><span class="our-tag">OUR</span> {change['our_text']}</td>
    <td class="akbar"><span class="akbar-tag">THEIR</span> <span class="red">{change['their_text']}</span></td>
    <td><span class="badge-{change['severity']}">{change['verdict']}</span> {change['reason']}</td>
</tr>''')

with open('/tmp/comparison.html', 'w') as f:
    f.write('\\n'.join(html_parts))
```

Structure the HTML with:
- **Executive Summary** banner at top (cosmetic vs commercial vs critical counts)
- **Category A table**: Cosmetic changes (auto-accept, grey background)
- **Category B table**: Commercial changes (orange badge, needs review)
- **Category C table**: Critical changes (red badge, must reject/negotiate)
- **Proposed restructuring section** if the user wants to restructure definitions (e.g., Commencement Date vs Effective Date)

## Pitfalls

1. **Same filename ≠ same content.** Counterparties often return a modified document with the same filename. Always check file size first — a 3.3 MB file vs 21 KB means they likely embedded scans/images alongside the text.

2. **Gmail may truncate `webViewLink`.** When comparing Drive-stored documents, the `webViewLink` URL may show a truncated file ID (missing trailing characters). Use the `id` field from `drive.files().list()` as the authoritative ID.

3. **python-docx via `uv`.** The system Python may lack `pip`. Install via `uv pip install python-docx`. The library installs into the venv at `/opt/hermes/.venv/` — run the script with `/opt/hermes/.venv/bin/python3`.

4. **Paragraph numbering may shift.** A blank paragraph inserted/deleted shifts all subsequent paragraph indices between versions. Use sequential matching (difflib) rather than comparing by index.

5. **LESSOR vs LESSORS inconsistency.** In Indian lease deeds, counterparties often globally replace "LESSOR" with "LESSORS" (pluralising the collective reference). This is cosmetic unless it changes obligation language in specific clauses — flag it once, don't repeat across every clause.

6. **Crossed-out amounts in tracked changes.** Some edits appear as inline "strikethrough+insert" in the raw text (e.g., `Rs. 6,00,000/-Rs. 12,00,000/-`). These are tracked changes that didn't get accepted. Always check for both values in a single string.

7. **Statutory clause removal.** Counterparties sometimes delete entire clauses by truncation (e.g., clause 11.3 and 11.4 being merged into garbled text). Check for missing clause numbers when the paragraph count differs between versions.

8. **Voice-note entity names.** When the user dictates the request via voice (STT), verify the counterparty name, project name, and email addresses against actual Gmail data before searching — see `google-workspace` skill's "Voice-message draft must verify" pitfall.

9. **`/tmp/` cleanup between calls.** The `/tmp/` directory on Hermes may be cleaned between tool calls or between sessions. If you save comparison output to `/tmp/`, it may be gone before you can deliver it. Save to a persistent location like `/data/hermes/` or deliver via MEDIA: immediately after creation. When re-downloading attachments in a later turn, the directory may no longer exist — always `os.makedirs()` before writing.

10. **Unicode smart quotes vs straight quotes.** Indian legal DOCX files frequently use Unicode curly quotes (`'` U+2019 RIGHT SINGLE QUOTATION MARK for apostrophe; `"` U+201C/U+201D for double quotes). Python string replacement using regular `'` / `"` will NOT match these. Always check the repr() of the paragraph text first to identify quote characters, then use the actual Unicode character or a double-pass:

    ```python
    # Check what quote characters are in the document
    print(repr(doc.paragraphs[55].text[:50]))
    # 'The LESSOR\u2019s obligation...'  ← Unicode RIGHT SINGLE QUOTATION MARK
    
    # Replace with the actual character:
    new_t = t.replace('LESSOR\u2019s', 'LESSORS\u2019')
    # OR normalize both sides:
    new_t = t.replace('\u2019', "'").replace("LESSOR's", "LESSORS'")  # convert to straight first
    ```

11. **python-docx `.paragraphs` index stability.** `doc.paragraphs` returns a new iterator each time you access it. You cannot do `doc.paragraphs.index(para)` to find a paragraph's index — it will raise ValueError. Store the index when iterating, or track indices explicitly.

12. **DOCX from different senders = wildly different file sizes.** A counterparty may return a document with the exact same filename but 100x the file size (21 KB vs 3.3 MB in one session). The large version may contain embedded scan images (signatures, old drafts, scanned affidavits) that inflate the DOCX zip. Always check file size and check for embedded images via `zipfile.ZipFile.namelist()` before assuming the extra bytes are textual changes.

13. **Coloured-text changes ≠ tracked changes.** Counterparties may use red/blue font colour to indicate changes instead of w:ins/w:del track changes. python-docx's Document() does NOT expose the original XML formatting — you MUST parse `word/document.xml` from the zip directly using ElementTree. Check for both:

   - `w:rPr/w:color[@w:val='FF0000']` (red = deletion / change)
   - `w:rPr/w:color[@w:val='0000FF']` (blue = insertion, though less common)
   - Named colours like `'red'`, `'blue'` also appear in some editors

   When you detect coloured-text changes, the `has_red` flag on a paragraph tells you the counterparty deliberately changed it — but paragraphs WITHOUT red text that still differ from our version may be cascading edits (e.g., grammar agreement changes when LESSOR→LESSORS). Flag these separately.

14. **Crossed-out amounts appear as merged text, not formatting.** A line like `Rs. 6,00,000/-Rs. 12,00,000/-` means the old value (Rs. 6L) was never struck through — it was simply left in place and the new value appended. The counterparty's editor rendered it as a single string. When you see doubled amounts, regex-extract both values:
    ```python
    import re
    amounts = re.findall(r'Rs\.\s*[\d,]+/-', text)
    # amounts[0] = old, amounts[1] = new (if two found)
    ```

15. **Clause deletion by truncation.** When counterparties delete a clause, sometimes the text of two adjacent clauses gets merged into one (e.g., Clause 11.3 content disappears and Clause 11.4 text appears where 11.3 should be). Check the sequential matching output for "replace" opcodes where the new text length is roughly equal to two clauses — this signals a deletion that collapsed numbering.

### Phase 5: Produce updated DOCX from comparison

After the user reviews changes and decides what to accept/reject, produce an **updated DOCX** with agreed changes applied. This closes the loop: compare → classify → edit → deliver.

**Setup:**

```bash
uv pip install python-docx
```

**Modifying paragraphs in an existing DOCX:**

python-docx `Document()` preserves the original formatting (fonts, bold, spacing, tables) when you modify text. The key technique is to update `runs[0].text` and clear all subsequent runs:

```python
from docx import Document

doc = Document('/path/to/original.docx')

def set_para_text(para_idx, new_text):
    """Replace the text of a paragraph at a given index, preserving formatting."""
    para = doc.paragraphs[para_idx]
    if para.runs:
        para.runs[0].text = new_text
        for run in para.runs[1:]:
            run.text = ''
    else:
        para.add_run(new_text)

# Apply changes
set_para_text(7, '(1) Mr. M Akber Hussain, PAN: AASPH6349B, holding an undivided 30% share;')
set_para_text(12, doc.paragraphs[12].text.replace('"LESSOR"', '"LESSORS"'))

# For regex replacements across runs (e.g. removing a struck-through value):
import re
def clean_amount_string(text):
    """Fix merged tracked-change amounts: 'Rs. 6,00,000/-Rs. 12,00,000/-' → 'Rs. 12,00,000/-'"""
    amounts = re.findall(r'Rs\.\s*[\d,]+/-', text)
    if len(amounts) >= 2:
        return text.replace(amounts[0], '').strip()  # remove the old value
    return text

doc.save('/tmp/updated_lease.docx')
```

**Common modification patterns for lease deeds:**

| Pattern | Code |
|---------|------|
| Global find-replace (LESSOR → LESSORS) | `t = p.text.replace('LESSOR', 'LESSORS')` |
| Name update in specific paragraph | `t = p.text.replace('Sara Hussain', 'Sara Banu Hussain')` |
| Pluralise verb agreement | `t = p.text.replace('has accepted', 'have accepted')` |
| Restructure definition paragraphs | Replace entire paragraph text (P35 → new text) |
| Fix merged amounts | Regex to keep only the new value |
| Delete a sentence | `.replace('entire clause text to remove', '')` |

**Commencement Date restructuring pattern** (common in Indian lease-deed negotiations):

When the user wants to split the definition:

| Original Concept | Renamed To | Definition |
|-----------------|------------|------------|
| Execution/registration date | "Lease Commencement Date" | The date the deed is registered |
| Occupation trigger date | "Effective Date" / "Occupation Date" | Earlier of (i) LESSEE takes occupation or (ii) 6 months from Lease Commencement Date |
| 7-year term | "Lease Term" | 7 years from Effective Date |

Implementation:

```python
# Before (combined definition):
p35.text = '...shall commence from the date of execution... (the "Commencement Date"), subject to...'
p36.text = '(i) the date of occupation... or (ii) 6 months from execution... 7 years from the Commencement Date'

# After (split):
set_para_text(35, 'This Lease Agreement shall commence from the date of execution of this Deed (the "Lease Commencement Date").')
set_para_text(36, 'For the purposes of computing all timelines, rent periods, and the Lease Term under this Agreement, the term "Effective Date" shall mean the earlier of: (i) the date the LESSEE takes occupation of the Leased Premises, or (ii) the date falling Six (6) months from the Lease Commencement Date. The lease shall be valid for a period of Seven (7) years from the Effective Date (the "Lease Term"), unless earlier terminated in accordance with the provisions of this Agreement.')

# Then update all rent timeline references to use the new defined term:
for idx in [42, 43, 44]:  # rent schedule paragraphs
    t = doc.paragraphs[idx].text
    set_para_text(idx, t.replace('from the date of executing and registering this deed', 'from the Lease Commencement Date'))
```

**Preserving table content** (lease deeds often have Schedule tables):

```python
for ti, table in enumerate(doc.tables):
    for ri, row in enumerate(table.rows):
        for ci, cell in enumerate(row.cells):
            for para in cell.paragraphs:
                for run in para.runs:
                    run.text = run.text.replace('OLD TEXT', 'NEW TEXT')
```

**Verification after modification:**

After saving, re-read the file and print key paragraphs to verify:

```python
doc2 = Document('/tmp/updated.docx')
for idx in [7, 10, 12, 35, 36]:  # pick 5-10 representative indices
    print(f"P{idx}: {doc2.paragraphs[idx].text[:100]}")
```

## Related Skills

- `google-workspace` — retrieving email attachments and Drive files
- `ocr-and-documents` — extracting text from PDFs that can't be opened with python-docx
- `powerpoint` — comparing PPTX files (uses python-pptx instead of python-docx)

## Reference Files

- `references/lease-deed-comparison-worked-example.md` — Worked example from Jul 15 session (standard track-changes comparison)
- `references/red-text-and-html-output-worked-example.md` — Worked example from Jul 17 session (red-text changes without track changes, HTML comparison table output)
- `references/docx-modification-worked-example.md` — Worked example from Jul 17 session (producing updated DOCX after comparison, restructuring Commencement Date, applying cosmetic + commercial changes)
