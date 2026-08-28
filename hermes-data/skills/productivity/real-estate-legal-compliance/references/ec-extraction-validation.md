# EC Data Extraction Validation

When transaction data extracted from a Tamil Nadu Encumbrance Certificate PDF doesn't match expected counts, use this investigation workflow.

## Known Pattern: Misleading Filenames

**Verified on:** Westbury Hospitality EC (Kagganur Sy.93, Jul 2026)

The file was named `Westbury_Hospitality_EC_187_Transactions.pdf` (136 pages) but the actual EC certificate stated **Number of Entries: 161** in its footer. The filename "187" was incorrect — the true entry count was 161. **Never trust the filename for the transaction count.**

## Validation Workflow

### Step 1: Cross-Validate Extraction Engines

Extract with both pymupdf and pdftotext to confirm they agree:

```python
# pymupdf
import fitz
doc = fitz.open(pdf_path)
all_text = ""
for page in doc:
    all_text += page.get_text()

# pdftotext (CLI)
import subprocess
result = subprocess.run(["pdftotext", pdf_path, output_path], capture_output=True)
```

If both produce the same count of document numbers (format `NNNN/YYYY`), the extraction is reliable.

### Step 2: Check the Official EC Footer

Every Tamil Nadu EC ends with a footer:

```
Number of Entries/பதிவுகளின் எண்ணிக்கை: NNN
```

This is the authoritative count from the Registration Department. Read it from the last few pages of the PDF (usually page 135 in a 136-page document).

```python
# Find the footer
m = re.search(r'Number of Entries[^:]*:\s*(\d+)', full_text)
official_count = int(m.group(1)) if m else None
```

### Step 3: Map Serial Numbers vs Document Numbers

EC entries have two numbering schemes:

| Number | Format | Purpose |
|--------|--------|---------|
| **Sr.No** | 1, 2, 3... N | Sequential entry number, appears in column 1 of the table |
| **Document No** | NNNN/YYYY | Registered document number (e.g. `2376/2025`) |

A Sr.No may appear **twice** per entry:
- **Entry start** — near the beginning of the entry, followed by Document No + 3 dates
- **Mid-entry continuation marker** — appears later near "Boundary Details" or "Schedule 1 Details" (page continuation reference in the table layout)

```python
# Find all doc numbers — use broad pattern (1-4 digits, not just 4)
doc_numbers = []
for i, line in enumerate(lines):
    if re.match(r'^\d{1,4}/202[56]$', line.strip()):
        doc_numbers.append(line.strip())

# Find all potential serial numbers and distinguish entry starts
sr_numbers = []
for i, line in enumerate(lines):
    if line.strip().isdigit() and 1 <= int(line.strip()) <= official_count:
        sr = int(line.strip())
        after = ' '.join(lines[i+1:i+5]).strip()
        # Check if followed by a date (entry start marker)
        has_date = bool(re.search(r'\d{2}-\w{3}-\d{4}', after))
        # Exclude mid-entry references (near Boundary/Schedule)
        is_mid_entry = any(kw in after[:80] for kw in 
            ['Schedule 1 Details', 'Boundary Details', 'Plot No.', 'Property Type', 'Village &'])
        if has_date and not is_mid_entry:
            sr_numbers.append(sr)
```

### Step 4: Calculate the Gaps

```
Official entries (EC footer)     = N
Document numbers found           = D
Gap (entries without doc number) = N - D
```

Typical reasons for entries without document numbers:
- **Cancelled entries** — a document was presented and then cancelled; has Sr.No but no document number
- **Administrative entries** — internal registration office notations
- **OCR gaps** — document number was split across a page break or merged table cell and the text extraction missed it
- **Short doc numbers (most common)** — If using `^\d{4}/202[56]$` regex, entries with 1-3 digit doc numbers like `51/2026` are missed. Always re-check with `^\d{1,4}/202[56]$` before reporting gaps. In the Westbury EC, the initial reported gap of 12 narrowed to only 4 after broadening the regex.

### Step 5: Visual Verification on Ambiguous Pages

When text extraction produces uncertain results, convert specific PDF pages to images and use vision_analyze:

```python
import fitz
doc = fitz.open(pdf_path)
for page_num in range(doc.page_count):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=200)
    pix.save(f"/tmp/page_{page_num+1}.png")
doc.close()
```

Then use `vision_analyze` on key pages (around the suspected missing entries) to visually read the table.

### Step 6: Report Findings Clearly

```
Expected: 187 (from filename)
Official: 161 (EC footer — authoritative)
Found:    149 (document numbers NNNN/YYYY extracted)
Gap:      12  (161 - 149 = entries with Sr.No but no document number)
```

## Key Pitfalls

| Pitfall | Description |
|---------|-------------|
| **Filename trust** | The filename might say "187 Transactions" but the EC itself says 161. Never trust the filename over the document. |
| **Double-counting Sr.No** | Each entry's Sr.No appears twice — at entry start AND as mid-entry page continuation marker. Filter by "has date nearby and not near Boundary/Schedule" to get true entry starts. |
| **Serial number spacing** | In OCR text, the Sr.No can be 10+ lines away from its document number due to the table layout (parties listed in left column span many lines). Look-back of 3-5 lines may miss it — use a wider window (10-15 lines) or check by date proximity instead. |
| **OCR quality on scanned ECs** | Tamil Nadu ECs have mixed Tamil/English table headers and small font sizes. pymupdf's get_text() extracts embedded text but may miss table cell boundaries. pdftotext produces more lines but same content. For truly problematic pages, visual inspection is the fallback. |
| **Document number format change** | Some entries may use document numbers in a different format (e.g., from an older year like NNNN/2024) that the regex `\\d{4}/202[56]` would miss. Adjust the year pattern if the EC spans multiple years. |
| **Short document numbers** | TN ECs do NOT pad document numbers to 4 digits — `51/2026`, `216/2026` and even `9/2026` are valid. The regex `^\\d{4}/202[56]$` will MISS these. Use `^\\d{1,4}/202[56]$` instead. In the Westbury EC (Jul 2026), 14 of 149 document numbers were short-format (1-3 digits), and using the 4-digit-only regex caused 8 false \"missing entries.\" |

## Tools & Commands

```bash
# pdftotext — cross-validate extraction
pdftotext input.pdf output.txt
wc -l output.txt

# pymupdf — extract with positional awareness
python3 -c "
import fitz
doc = fitz.open('input.pdf')
for p in doc:
    print(f'===PAGE {p.number+1}===')
    print(p.get_text())
"

# pymupdf — page count only
python3 -c "import fitz; print(fitz.open('input.pdf').page_count)"
```

## Reference Session

- **July 15-16, 2026:** Westbury Hospitality EC (Kagganur Sy.93, Palm Paradise layout, Hosur/Krishnagiri, TN). 136 pages. Official entries: 161. Document numbers found: 149 (with 4-digit regex). Short doc numbers found: 14 entries (e.g. `9/2026`, `51/2026`, `216/2026`). After broadening to `^\d{1,4}/202[56]$`, truly missing: only 4 entries (Sr.No 40, 104, 112, 127). Filename claimed 187 — was incorrect by 26.
