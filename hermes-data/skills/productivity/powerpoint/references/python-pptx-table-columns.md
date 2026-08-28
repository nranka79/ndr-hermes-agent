# python-pptx — Adding Columns to an Existing Table

## Problem

You have an existing PowerPoint table (e.g., a Price Comparison table with 5 columns) and need to add 3 new columns (Location, Launch Date, Completion/Status). python-pptx has no `add_column()` method on tables — you must extend the table via direct XML manipulation.

## Quick Solution

```python
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.oxml.ns import qn
from lxml import etree

prs = Presentation("input.pptx")
slide = prs.slides[SLIDE_INDEX]

for shape in slide.shapes:
    if not shape.has_table:
        continue
    table = shape.table
    tbl_el = table._tbl
    
    # Step 1: Add/replace column definitions in the grid
    gridCols = tbl_el.find(qn('a:tblGrid'))
    # Clear existing, add all columns with desired widths
    for gc in list(gridCols.findall(qn('a:gridCol'))):
        gridCols.remove(gc)
    new_widths = [2000000, 900000, 1300000, 1300000, 800000, 2000000, 850000, 1400000]
    for w in new_widths:
        col_el = etree.SubElement(gridCols, qn('a:gridCol'))
        col_el.set('w', str(w))
    
    # Step 2: Add cells to each existing row
    for r_idx, tr in enumerate(tbl_el.findall(qn('a:tr'))):
        for c_idx in range(NUM_NEW_COLUMNS):
            tc = etree.SubElement(tr, qn('a:tc'))
            # Build cell content with proper txBody structure
            txBody = etree.SubElement(tc, qn('a:txBody'))
            bodyPr = etree.SubElement(txBody, qn('a:bodyPr'))
            lstStyle = etree.SubElement(txBody, qn('a:lstStyle'))
            p = etree.SubElement(txBody, qn('a:p'))
            run = etree.SubElement(p, qn('a:r'))
            t = etree.SubElement(run, qn('a:t'))
            t.text = "Cell content"
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    break

prs.save("output.pptx")
```

## Complete Example: Adding 3 Data Columns with Styling

Used in a 13-project real estate market research deck to add **Location**, **Launch Date**, and **Completion/Status** to an existing 5-column Price Comparison table.

### Data Structure

```python
projects_data = {
    1: ["Nandi Hills Road, Karahalli Post", "2022", "Ready to Move (2026)"],
    2: ["Doddaballapur Road / Nandi Hills", "2023", "Under Construction"],
    # ... row 7 is separator, handled separately
    14: ["Off Doddaballapur Road, Devanahalli", "2022", "Ready to Move"],
}
```

### Cell Builder Function (XML-level)

```python
def set_cell_style(tc, text, font_size=Pt(8), bold=False, bg_color=None, fg_color="000000", align="left"):
    """Create a fully styled table cell from an lxml <a:tc> element."""
    if bg_color:
        tcPr = tc.find(qn('a:tcPr'))
        if tcPr is None:
            tcPr = etree.SubElement(tc, qn('a:tcPr'))
        for old in tcPr.findall(qn('a:solidFill')):
            tcPr.remove(old)
        solidFill = etree.SubElement(tcPr, qn('a:solidFill'))
        srgbClr = etree.SubElement(solidFill, qn('a:srgbClr'))
        srgbClr.set('val', bg_color)
        tcPr.set('marL', str(Emu(45720)))
        tcPr.set('marR', str(Emu(45720)))
        tcPr.set('marT', str(Emu(22860)))
        tcPr.set('marB', str(Emu(22860)))
    
    for old in tc.findall(qn('a:txBody')):
        tc.remove(old)
    
    txBody = etree.SubElement(tc, qn('a:txBody'))
    bodyPr = etree.SubElement(txBody, qn('a:bodyPr'))
    lstStyle = etree.SubElement(txBody, qn('a:lstStyle'))
    p = etree.SubElement(txBody, qn('a:p'))
    
    al = {"left": "l", "center": "ctr", "right": "r"}[align]
    pPr = etree.SubElement(p, qn('a:pPr'))
    algn = etree.SubElement(pPr, qn('a:algn'))
    algn.set('val', al)
    
    run = etree.SubElement(p, qn('a:r'))
    rPr = etree.SubElement(run, qn('a:rPr'))
    sz = etree.SubElement(rPr, qn('a:sz'))
    sz.set('val', str(int(font_size.pt * 100)))
    if bold:
        etree.SubElement(rPr, qn('a:b'))
    
    if fg_color and fg_color != "000000":
        sf = etree.SubElement(rPr, qn('a:solidFill'))
        sc = etree.SubElement(sf, qn('a:srgbClr'))
        sc.set('val', fg_color)
    
    t = etree.SubElement(run, qn('a:t'))
    t.text = text
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
```

### Applying Styles Per Row

```python
HEADER_BG = "1F3864"; HEADER_FG = "D4AF37"
SEPARATOR_BG = "D9D9D9"
VILLA_BG = "E2EFDA"; PLOT_BG = "D6E4F0"

for r_idx, tr in enumerate(tbl_el.findall(qn('a:tr'))):
    if r_idx == 0:
        bg, fg, bold, fs = HEADER_BG, HEADER_FG, True, Pt(9)
    elif r_idx == 7:  # separator
        bg, fg, bold, fs = SEPARATOR_BG, "000000", False, Pt(8)
    elif r_idx < 7:   # villas
        bg, fg, bold, fs = VILLA_BG, "000000", False, Pt(8)
    else:             # plots
        bg, fg, bold, fs = PLOT_BG, "000000", False, Pt(8)
    
    for c_idx, col_name in enumerate(["Location", "Launch Date", "Completion/Status"]):
        tc = etree.SubElement(tr, qn('a:tc'))
        if r_idx == 0:
            set_cell_style(tc, col_name, font_size=Pt(9), bold=True, bg_color=HEADER_BG, fg_color=HEADER_FG, align="center")
        elif r_idx == 7:
            set_cell_style(tc, "", bg_color=SEPARATOR_BG)
        else:
            data = projects_data.get(r_idx, ["—", "—", "—"])
            set_cell_style(tc, data[c_idx], font_size=Pt(8), bg_color=bg, align="center")
```

## How Table Extension Works (XML Architecture)

A PowerPoint table in OPC XML has this structure:

```
<a:tbl>
  <a:tblGrid>
    <a:gridCol w="2000000"/>
    <a:gridCol w="900000"/>
    ...
  </a:tblGrid>
  <a:tr>
    <a:tc>...</a:tc>
    <a:tc>...</a:tc>
    ...
  </a:tr>
  ...
</a:tbl>
```

To add columns:
1. Add `<a:gridCol>` to `<a:tblGrid>` — defines new column widths
2. Add `<a:tc>` to each `<a:tr>` — provides cell content
3. Cell order in each row must match gridCol order

**Cells are appended at end.** If table had 5 columns and you add 3 new tc elements, cells 0-4 are originals and cells 5-7 are new ones.

## Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| Column widths too wide | Added widths without reducing existing ones | Sum must fit within ~12,000,000 EMU (slide content area) |
| Missing margins on new cells | `marL`/`marR` not set | Add to `tcPr` attributes |
| White text on light bg (invisible) | Default fg_color but colored bg | Always set both `bg_color` and `fg_color` |
| Font size wrong | Setting `sz` raw | Use `str(int(font_size.pt * 100))` |

## Verification

```python
prs2 = Presentation(output)
for shape in prs2.slides[SLIDE_INDEX].shapes:
    if shape.has_table:
        t2 = shape.table
        print(f"{len(t2.rows)} rows x {len(t2.columns)} cols")
        for r in range(len(t2.rows)):
            vals = [t2.cell(r, c).text.strip()[:30] for c in range(len(t2.columns))]
            print(f"  Row {r}: {' | '.join(vals)}")
        break
```
