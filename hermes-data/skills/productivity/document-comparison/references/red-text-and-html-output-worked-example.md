# Worked Example: Red-Text Change Detection + HTML Output (Miller's Road, Jul 17 2026)

Session date: 2026-07-17
Documents: Same lease deed as prior session, but new version returned with **red-text changes** instead of track changes.

## The Context

The user received the lease deed back from Akbar's team (Atheeq at padirector@ahindia.com). They claimed "minor corrections" but actually made significant commercial changes — doubling the security deposit, changing renewal from a right to a request, adding prior-approval to sub-letting.

Their changes were indicated in **red font colour** — not track changes (no w:ins/w:del elements in the XML).

## Key Difference: No Track Changes

```python
# Check if a DOCX has proper track changes
import zipfile
count = content.count('w:ins'), content.count('w:del')
# (0, 0) means NO track changes — changes were made in coloured text
```

When this happens, the only way to detect what changed is:
1. Parse the raw XML for run-level colour information (Phase 2A in SKILL.md)
2. Run a full paragraph-by-paragraph diff (Phase 3)
3. Correlate: paragraphs with red text = deliberately changed; paragraphs without red text but different = cascading / grammar edits

## Red-Text Detection Code (executed in this session)

```python
import zipfile
from xml.etree import ElementTree as ET
import re

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def get_paragraphs_with_runs(path):
    with zipfile.ZipFile(path, 'r') as z:
        with z.open('word/document.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
    
    paras = []
    for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
        full_text_parts = []
        run_details = []
        
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
        paras.append({'text': full_text, 'runs': run_details})
    
    return paras
```

## HTML Comparison Table Pattern

The file `/tmp/compare.html` was structured with three tables plus a summary:

### Categories in the HTML

| Category | Badge | Background | Treatment |
|----------|-------|-----------|-----------|
| **Cosmetic (auto-accept)** | `badge-accept` (green) | Grey/accepted rows | PAN fills, names, pluralisation, municipal numbers |
| **Commercial (review)** | `badge-commercial` (orange) | White/yellow highlight | Security deposit, rent-free period wording, utilities |
| **Critical (reject)** | `badge-critical` (red) | Red accent | Renewal right, sub-letting control, statutory clause deletion |

### HTML Structure

```
+-- Executive Summary (div.summary)
+-- Category A: Cosmetic — <table> with accepted changes
+-- Category B: Commercial — <table> with needs-review changes
+-- Category C: Critical — <table> with must-reject changes
+-- Proposed Restructuring — Callout box (if user wants to redefine terms)
```

### Key design choices
- Each change row shows **Our Version** (green background) vs **Their Version** (orange background, red text)
- The verdict column has a badge + one-liner reason
- Accept changes get merged into the "accepted" background colour
- Critical changes get bold red text in the "their version" column

## Output File Delivery

The HTML file was delivered via:
```
MEDIA:/tmp/lease_compare/Lease_Comparison_Akbar_vs_DRA.html
```

The user can open it in a browser directly from Telegram.

## Changes Discovered in This Session

| Change | Our | Their | Severity |
|--------|-----|-------|----------|
| GF Security Deposit | Rs. 6L | Rs. 12L | Critical |
| Aggregate SD | Rs. 30L | Rs. 36L | Critical |
| Renewal right | "right to renew" | "can request for renew" | Critical |
| Sub-letting | "absolute right" | "subject to prior approval" | Critical |
| 20% discount | Unconditional | "subject to value of investment" | Commercial |
| Clause 11.3 | Statutory charges | Entirely deleted (overwritten) | Critical |
| Commencement Date | 7 yrs from Commencement | 7 yrs "after 6 months rent free" | Commercial |
| Exit after lock-in | Notice only | Added fit-out forfeiture | Commercial |
| Utlities scope | Elec + water | Added Lift AMC + Gen Maintenance | Commercial |
