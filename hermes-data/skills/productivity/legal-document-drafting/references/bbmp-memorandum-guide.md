# BBMP Memorandum — PID Bifurcation & e-Khata Splitting

Trigger: user says "BBMP memorandum", "bifurcation request", "parent PID split", "individual e-Khata application", "fill this BBMP memo".

## What This Is

A BBMP Memorandum submitted by a developer to request:
- Bifurcation of the parent PID/Khata
- Allotment of separate e-PID numbers for each apartment unit
- Issuance of individual e-Khatas in the developer's name

Template name convention: `BBMP_Memorandum_<Company>_<Signatory>_Final.docx`

## Data Sources (on Drive) — extraction priority order

| Priority | Document | What It Provides | Extraction Method |
|---|---|---|---|
| 1 | **Property Tax Receipt** | Owner name, property address, Survey No, Old PID/Khata No, Ward | pdfminer (usually text) |
| 2 | **Fire NOC** | PID No, Survey No, full address, applicant address, building description | pdfminer (text-extractable post-2024) |
| 3 | **Occupancy Certificate** | Total residential units, floor-wise schedule, built-up areas, LP/OC ref numbers | pdfminer or OCR (pdftoppm + vision_analyze) |
| 4 | **Building Permit / Sanction Plan** | Survey No, Khata No, PID, Plot No, total floors/units, zone | Usually scanned — use OCR |
| 5 | **Sale Deeds** | Title chain, original khata holder | Scanned — OCR if needed |
| 6 | **Board Minutes / CoI** | Registered office, directors, CIN, DIN | pdfminer (text) |

## Template Structure (typical)

The BBMP Memorandum DOCX template typically has:
- **P0**: `MEMORANDUM` — large bold heading, separate paragraph
- **P1**: Everything else — all body text in a **single run** of one paragraph

This means filling the template = replacing P1's run text with the filled version.

## Field Mapping

| Field in Template | Extract From |
|---|---|
| `________________ Zone` | Fire NOC or Tax Receipt — zone name (e.g., "Central City Corporation") |
| `registered office at _________________` | Board Minutes / CoI OR Fire NOC applicant address |
| `Survey No. ___________` | Tax Receipt or Fire NOC |
| `Khata No. ___________` | Tax Receipt: column "Old PID No / Khatha / Survey No" |
| `PID No. ___________` | Same as Khata No (often identical for parent property) |
| `situated at _________________` | Tax Receipt "Property Address" or Fire NOC |
| `Mr. _______` (original khata holder) | Tax Receipt "Owner's Name" field |
| `project known as _________________` | OC Certificate or Covering Letters |
| `consisting of ____ units` | OC Certificate — count of residential apartments |
| `Project Name: _________________` | As above |
| `Property Address: ___________` | Fire NOC or Tax Receipt |
| `Survey Number(s): _________________` | From Tax Receipt |
| `Khata Number: _________________` | Old PID from Tax Receipt |
| `Existing Parent PID: _________________` | Same as Khata No (PID) |
| Schedule (13 rows) | OC Certificate floor-wise table |
| `Date: ____/____/20____` | Leave blank or fill current date |
| Signatory | Board Minutes (Director name + DIN) |

## Flat Numbering Convention (common pattern)

- Often sequential: 1001, 1002, 1003...1013 (not floor-based like 201, 301)
- Always confirm flat numbers with the user — do not assume floor-number convention
- The template may have 13 rows; actual unit count may differ — add/remove rows

## DOCX Generation Pattern

```python
from docx import Document

doc = Document('template.docx')
body_para = doc.paragraphs[1]  # P0 = heading, P1 = body

# Clear existing text
for run in body_para.runs:
    run.text = ''
body_para.runs[0].text = filled_body_text

doc.save('output.docx')
```

### Critical: Ampersand in string literals

The `&` character in a Python heredoc passed via `terminal()` causes a false-positive background-detection error. **Workarounds:**
1. Replace `&` with `and` in the body text (preferred for formal documents)
2. Write the script to a `.py` file first, then execute it

## Pdfminer + OCR Fallback Flow

```python
from pdfminer.high_level import extract_text

# Step 1: Try text extraction
text = extract_text(pdf_path)
if not text.strip():
    # Step 2: Convert to image and OCR
    # pdftoppm -png -r 200 input.pdf /tmp/output_prefix
    # Then use vision_analyze() on the PNG
```

**Known:** Some 2026-27 BBMP tax receipt PDFs are corrupt (missing /Root object) — skip and use earlier fiscal years.

## Pitfalls

- Unit count in OC may differ from actual flat numbering scheme — confirm with user
- Registered office may differ between Board Minutes ("No. 2") and Fire NOC ("No. 4") for the same building — ask user
- Schedule rows in template may not match actual unit count — adjust
- OC Certificate table may show residential units starting from 2nd floor (gym/lobby on 1st) — verify 1001 placement
- Ampersand (`&`) in terminal heredoc triggers background-detection — avoid or write to .py file
- "3BF+GF+13UF with 12 units" in OC = 3 basements + ground + 13 upper floors; units per floor count varies
- Flats starting with "10xx" can span floors 1–13: 1001 (1st floor) through 1013 (13th floor)
