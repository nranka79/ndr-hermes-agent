# Structural Stability Certificate — KRERA Workflow

The Structural Stability Certificate (also called Structural Stability Report) is a KRERA-required document distinct from Form-1 (CA), Form-2 (Architect), and Form-3 (Engineer). It is drafted by the **structural consultant** (not the architect or engineer) and certifies that the structural design is sound.

## Document Structure

The KRERA template contains these sections, each with blanks to fill:

| Section | Typical Content | Data Source |
|---------|----------------|-------------|
| Project & Survey | Name, survey nos, approved floors | Plan sanction, title docs |
| Design Criteria | Tower count, building use | Structural drawings (title block) |
| Building Height | Per-block heights | Architectural drawings |
| SBC (Safe Bearing Capacity) | kN/m² value at depth | Soil investigation report (also on structural dwgs) |
| Founding Level | Foundation type + depth (RL) | Structural drawings (section details) |
| IS Codes | Design codes used | Structural drawings (notes / title block) |
| Loads | DL, LL, WL, SL | Standard (per IS 875) |
| Structural System | RCC framed + shear walls | Structural drawings |
| Software | ETABS, SAFE, etc. | Standard for this class of building |
| Affirmation | Engineer's declaration | Standard text |

## Workflow

```
Find template on Drive
  → Find structural drawings in STRUCTURAL DWGS folder
  → Convert PDFs to images (pdftoppm)
  → Vision-analyze each page for:
     - Title block (project, consultant, date, scale)
     - General notes (SBC, IS codes, seismic zone)
     - Foundation details (footing type, dimensions)
     - Column/beam schedules
     - Section details (depths, levels)
  → Extract structural parameters
  → Fill document (all fill-ins in RED)
  → Upload to RERA folder
  → WhatsApp structural consultant/engineer for sign-off
```

## Data Extraction from Structural Drawings

### What the Structural Drawings Typically Show

| Parameter | Where to Find | Example |
|-----------|--------------|---------|
| Project name | Title block (first/last page) | "Proposed Residence for Mr. Amber" |
| Building config | General notes | "B+G+4 FLOOR" |
| SBC | General notes | "220 kN/m² at 2.5 m" |
| Foundation type | Foundation details sheet | Isolated footings OR raft |
| Footing dimensions | Footing schedule | 1.25×1.25m, 2.9×2.9m, etc. |
| Column sizes | Column schedule / legend | 0.2×0.6, 0.6×0.6 |
| Concrete grade | General notes / schedule | M25 |
| Steel grade | General notes / schedule | Fe500 |
| Seismic zone | General notes (or assumed) | Zone II (Bangalore) |
| Consultant name | Title block | RK Design Engineers |
| Drawing date | Title block | 08-12-2025 |
| Sheets count | Title block | "Sheet 1 of 22" |

### What Structural Drawings Do NOT Show

- **Survey numbers** — these come from registered documents (JDA, EC), not structural drawings
- **Building height in metres** — architectural drawings have this; structural dwgs say "Refer architectural drawing for dimensions and levels"
- **Founding level RL** (Reduced Level) — architectural drawings or soil report; structural dwgs show section details but often without RL values
- **Amenity block details** — if present, shown on architectural drawings

**Important:** Add a BLANK note in the certificate for any field that cannot be extracted, and mark "To be confirmed from architectural drawings / soil investigation report" in RED.

## The Raft vs Isolated Footings Trap

**The template says "raft" but many projects use isolated footings.** Do NOT trust the template — verify against the structural drawings:

- **Raft foundation:** One continuous slab under the entire building. Drawing shows a large slab with reinforcement both ways.
- **Isolated footings:** Individual pad footings under each column. Drawing shows a "FOOTING SCHEDULE" with per-footing dimensions and a detail labelled "TYPICAL ISOLATED FOOTING".

When changing "raft" to "isolated footings", rewrite the sentence completely. Example:

> *Original:* "The founding level of the raft is approximately ________, corresponding to the ground floor level at ___________."
>
> *Corrected:* "The founding level of the structure consists of isolated footings of varying depths, designed as per the soil investigation report. The bottom of footing level is approximately ________, corresponding to the ground floor level at ___________. [Note: Isolated footings confirmed from structural drawings — exact RL values to be confirmed from architectural drawings.]"

## DOCX Filling Technique (No python-docx)

When `python-docx` cannot be installed (e.g. permission-denied system venv), manipulate the DOCX XML directly:

```python
import zipfile, io, xml.etree.ElementTree as ET

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def add_red_run(para, text, bold=False):
    """Add a RED-colored run to a paragraph element."""
    r = ET.SubElement(para, f'{W}r')
    rPr = ET.SubElement(r, f'{W}rPr')
    color = ET.SubElement(rPr, f'{W}color')
    color.set(f'{W}val', 'FF0000')
    sz = ET.SubElement(rPr, f'{W}sz')
    sz.set(f'{W}val', '22')
    if bold:
        b = ET.SubElement(rPr, f'{W}b')
    t = ET.SubElement(r, f'{W}t')
    t.text = text
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

def clear_para_runs(para):
    """Remove all runs from a paragraph."""
    for run in list(para.findall(f'{W}r')):
        para.remove(run)

# Read docx as ZIP, modify document.xml, write back
with zipfile.ZipFile(docx_path, 'r') as z:
    xml_content = z.read("word/document.xml")

root = ET.fromstring(xml_content)
paragraphs = root.findall(f'.//{W}p')

for para in paragraphs:
    text = ''.join(t.text or '' for t in para.iter(f'{W}t'))
    if 'founding level of the raft' in text:
        clear_para_runs(para)
        add_red_run(para, 'Isolated footings text here...', bold=False)

# Serialize and write back
xml_bytes = ET.tostring(root, encoding='unicode')
with zipfile.ZipFile(io.BytesIO(original_docx), 'r') as zin:
    with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                zout.writestr(item, xml_bytes.encode('utf-8'))
            else:
                zout.writestr(item, data)
```

**Why this approach:**
- Works without `python-docx` (no pip install needed)
- Supports RED color formatting (not just text replacement)
- Can completely rewrite paragraphs rather than just fill blanks
- Can mix bold and normal text in the same paragraph
- Multiple styled runs per paragraph (bold labels + normal values)

## Sign-off Chain

1. **Structural consultant** (e.g. RK Design Engineers) prepares the certificate
2. **Project engineer** (e.g. Anbu / Anbarasan) reviews and signs
3. **Print → Sign → Scan → Seal → Scan again**
4. Upload final signed+sealed PDF to RERA Drive folder
5. The structural consultant may also need to provide their registration/license copy

## Related References

- `docx-form-filling.md` in `ocr-and-documents` skill — underscore placeholder replacement pattern (complementary; uses python-docx for simpler templates)
- `ranka-amber-data-map.md` — project-specific data used alongside structural info
- `rera-approval-documents` (absorbed into this umbrella) — Form-1/2/3 workflows
