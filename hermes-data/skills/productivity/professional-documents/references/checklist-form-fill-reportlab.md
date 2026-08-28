# Checklist / form-fill PDFs via reportlab (APF Checklist worked example)

Recurring DRAAS request: user sends a **blank bank/project checklist PDF**
(e.g. Axis Property Finance "APF Checklist" for Ranka Amber) plus a list of
which serial numbers are available ("Sr No shown here are available - 1..10,
13,14,15,16 / Other Documents - 5") and expects a **filled PDF** marking each
row Yes/No. reportlab (4.3.1 in the Hermes venv) is the right tool: no system
deps, perfect for landscape table forms. WeasyPrint may not be installed and
is overkill for grid forms anyway.

## Workflow

1. **Read the blank form**: `pdftotext -layout <blank>.pdf apf.txt` — the
   checklist structure (Sr No | Documents | File Login | Available in File
   Sales/Credit columns) comes out as plain text. Reconstruct the rows into a
   Python list of `(sr, text, mandatory)` tuples per section (Title Related
   Documents, Region Specific, Plan/Approvals, Other Documents). Keep the
   user's own wording for the doc descriptions. **"Other Documents" items are
   multi-row**: item 1 spans 5 NOC sub-rows (Environment/Aviation/Fire/
   Pollution/NGT) that share the Sr cell, and long items (2, 4, 6) wrap — keep
   them as one logical row per Sr, blank Sr for the sub-rows.

2. **Parameterize the generator from the start** — one script, constants at
   top, because the user WILL iterate (add an item, add builder name, new
   project) and every correction is a 5-second rebuild:
   ```python
   PROJECT_NAME = "RANKA UDAYA"
   BUILDER_NAME = "DRA THINDLU LAND PARTNERS"
   AVAILABLE_TITLE = {"1","3","7","8","9","10","11"}
   AVAILABLE_REGION = {"13","14","15","16"}
   AVAILABLE_OTHER = {"5","6"}
   NA_TITLE = {"2","4","5","6"}        # explicit NA items
   ```
   Output filename embeds the project name (`APF_Checklist_<Project>_Filled.pdf`).

3. **Map availability as STRING-keyed sets**:
   ```python
   AVAILABLE_TITLE = {"1","2","3","4","5","6","7","8","9","10"}
   AVAILABLE_REGION = {"13","14","15","16"}
   AVAILABLE_OTHER = {"5"}          # "Other Documents" items have their own numbering
   ```
   ⚠️ **PITFALL (hit 2026-08-13):** Sr numbers extracted from the PDF text are
   strings; if you write `AVAILABLE_TITLE = {1,2,3,...}` (ints), every row
   silently renders "No" and the bug is invisible until you grep the output.
   Always string-key. If you do hit it, fix the sets and rebuild — don't try
   to cast in the comparison.

4. **Three status states — Yes / NA / No** (Ranka Udaya introduced NA,
   2026-08-13): the user's availability line may contain `NA` placeholders
   ("1,NA,3,NA,NA,NA,7,8,9,10,11,13,14,15,16"). Render NA rows AMBER
   (`colors.Color(0.98,0.92,0.80)`), Yes rows GREEN (0.85,0.95,0.85), No
   plain — and report all three buckets in the delivery summary. `mk_status`
   checks NA first, then availability:
   ```python
   def mk_status(sr, kind):
       if kind == 'title' and sr in NA_TITLE:
           return ("NA", "NA")
       avail = sr in (AVAILABLE_TITLE if kind == 'title' else
                      AVAILABLE_REGION if kind == 'region' else
                      AVAILABLE_OTHER if kind == 'other' else {"16"})
       return ("Yes" if avail else "No",) * 2
   ```

5. **Build with reportlab**: `SimpleDocTemplate(pagesize=landscape(A4))`,
   header info table (Name of Project - prefilled; Date/Builder/Sales
   Channel left blank for manual fill — but prefill Builder once the user
   gives it, e.g. "DRA Realty Pvt Ltd, Bangalore"), one grid per section with
   `TableStyle`:
   - `GRID 0.5 black`, `FONTNAME Helvetica 7.5-8pt`, `VALIGN TOP`
   - GREEN background on available rows (`colors.Color(0.85,0.95,0.85)`) +
     Helvetica-Bold on the Yes cells; AMBER on NA rows; light blue header band
   - Section headings via `Paragraph` with `spaceBefore`
   - Footer: italic "All non mandatory documents need to be provided in one
     go." + Verified by / Sales Manager-TL / CPC Login-Desk signature table

6. **Verify before delivering** (never trust the build):
   - `pdftotext -layout out.pdf - | grep -E "Yes|NA"` → assert the Yes rows are
     exactly the available set, NA rows are the NA set (and the No rows are the rest)
   - `pdftoppm -png -r 80 out.pdf apfpage` → `vision_analyze` page 1 + 2:
     alignment of the Yes/No columns (rightmost two), no overlapping text,
     signature block present

7. **Deliver via MEDIA: in the response text** — `MEDIA:/tmp/<name>.pdf` on
   its own, NOT via the `send_message` tool (that fails with cross-user-block /
   unknown-platform errors on this platform; the response-text MEDIA: pattern
   is the sanctioned delivery path). Summarize the marked-available items and
   the pending ones in the reply.

## CRITICAL: Paragraph-wrap every text cell (column overflow bug)

**PITFALL (hit 2026-08-13, user complained "Check the Alignments, its overriding the other columns"):** if you feed reportlab Table cells **plain strings**, long document descriptions (item 2, 6, 12.x, "Other" block) overflow their column and visually collide with the File Login / status columns. Fix: wrap EVERY text cell in a `Paragraph` with a small style — reportlab then wraps inside the column:

```python
cell_style = ParagraphStyle('cell', fontName='Helvetica', fontSize=7.5, leading=9)
data.append([Paragraph(sr, cell_style), Paragraph(text, cell_style),
             Paragraph(mand, cell_style), sales, credit])
```

Verify alignment visually after ANY multi-project rebuild (`pdftoppm` + vision on both pages, specifically checking long-text rows wrap inside Documents column and Yes/NA stay in the rightmost two).

## NOC sub-rows: give them explicit keys so they inherit item status

"Other Documents" item 1 spans 5 NOC sub-rows. If you give sub-rows `sr=""`, they render "No" even when item 1 is NA (or blank). **PITFALL (hit 2026-08-13):** give sub-rows explicit keys (`"1","1a","1b","1c","1d"`) and add them to the NA/blank sets individually:

```python
other_rows = [
    ("1",  "NOC from - Environment Clearance If Applicable", "..."),
    ("1a", "NOC from - Aviation departments If Applicable", "..."),
    ("1b", "NOC from - Fire Clearance If Applicable", "..."),
    ("1c", "NOC from - State / Central Pollution Board If Applicable", "..."),
    ("1d", "NOC from - NGT If Applicable", "..."),
    ("2",  "Builder Data Sheet / Annexure 1 ...", "..."),
    ...
]
# Ranka Oasis: user said "other - NA,NA,NA,,NA,5,NA,NA,(blank),(blank)" →
# NOC block NA except Pollution(1c) blank, KYC(5) Yes, BDS(2)/Bank(3)/Inv(6)/Price(7) NA,
# Payment(4)/Decl(8)/Visit(9) blank
cfg["other_na"]    = {"1","1a","1b","1d","2","3","6","7"}
cfg["other_blank"] = {"1c","4","8","9"}
```

## FOUR status states — Yes / NA / BLANK / No

Ranka Oasis (2026-08-13) introduced `(blank)` / empty placeholders in the availability line (`"NA,NA,NA,,NA,5,NA,NA,(blank),(blank)"`). The user's positional list format: **numbers = Yes, `NA` = amber, empty slot / `(blank)` = leave cell empty, anything else = No**. Render blank as `("", "")` (no fill), and still report all four buckets in the delivery summary. Keep NA checked first, then blank, then availability:

```python
def mk_status(sr, kind, cfg):
    if kind == 'title' and sr in cfg["title_na"]:
        return ("NA", "NA")
    if kind == 'other':
        if sr in cfg["other_na"]:
            return ("NA", "NA")
        if sr in cfg.get("other_blank", set()):
            return ("", "")
        avail = sr in cfg["other_yes"]
    ...
```

## Shared PROJECTS config dict + DOCX companion

Once a THIRD project arrives, refactor flat constants into a `PROJECTS` dict keyed by slug (`Ranka_Amber`, `Ranka_Udaya`, `Ranka_Oasis`), each with `project`, `builder`, `out`, and per-section Yes/NA/blank sets. Guard the build loop with `if __name__ == "__main__":` so a second script can `from make_apf_checklist import PROJECTS, ...` to build the editable DOCX:

```python
# make_apf_docx.py — build BOTH formats from the SAME config (never duplicate)
from docx import Document
from docx.shared import Pt
from docx.enum.table import WD_TABLE_ALIGNMENT
# add_row(): vals + bold + fill via w:shd (D9EAD3 green / FCE5CD amber)
# build_docx(cfg): title para, 3x2 info table (project/builder prefilled),
#   5-col Table Grid table (Sr|Documents|File Login|Sales|Credit), section
#   headings, green/amber shaded rows, italic note, signature table
out = cfg["out"].replace(".pdf", ".docx")
```

User's phrase "or generate a doc file to edit as required" = deliver BOTH PDF + DOCX. Verify docx by reopening with python-docx and asserting row count + KYC status cell (`d.tables[1]`, grep `KYCs` row for `('Yes','Yes')`).

## Iterative correction loop (expect it)

The user reviews the filled PDF and replies with deltas — handle each as a
constant edit + rebuild, deliver the new PDF in the same message:
- "11 is available" → add `"11"` to `AVAILABLE_TITLE`, rebuild
- "Builder Name : DRA Realty Pvt Ltd Bangalore" → set `BUILDER_NAME`, rebuild
- A whole new project line ("PROJECT NAME: RANKA UDAYA / DEVELOPER: DRA
  THINDLU LAND PARTNERS / CHECKLIST - AVAILABLE - 1,NA,3,... / other
  documents - 5,6") → change the constants, same script, new output file.
  Do NOT fork the script per project.

## Result shape (2026-08-13 worked examples)

- Ranka Amber APF Checklist: 16 items marked Yes (Title 1–10, Region 13–16,
  Other item 5 KYC), everything else No. Output:
  `/tmp/APF_Checklist_Ranka_Amber_Filled.pdf` (2 pages landscape).
- Ranka Udaya APF Checklist: Yes on Title 1,3,7,8,9,10,11 + Region 13–16 +
  Other 5,6; NA on Title 2,4,5,6; No on the rest. Output:
  `/tmp/APF_Checklist_Ranka_Udaya_Filled.pdf`.
- Ranka Oasis - Hosur APF Checklist (introduced blank + DOCX companion):
  Yes on Title 1,2,3,4,7,8,9,10,11 + Region 13,14,15 + Plan 16,18 + Other 5
  (KYC); NA on Title 5,6,12-block,17 + Other 1/1a/1b/1d (NOC),2,3,6,7; BLANK
  on Other 1c (Pollution),4,8,9; No on the rest. Outputs:
  `/tmp/APF_Checklist_Ranka_Oasis_Filled.pdf` + `.docx`. The full generator
  lives at `/tmp/make_apf_checklist.py` (PROJECTS dict with Amber/Udaya/
  Oasis) + `/tmp/make_apf_docx.py` — copy both as the starting point for the
  next project.
