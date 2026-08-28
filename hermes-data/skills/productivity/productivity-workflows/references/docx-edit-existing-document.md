# Editing Existing Word Documents (.docx) with python-docx

Programmatically edit existing Word documents: find-and-replace text, insert new paragraphs, delete sections, update headers — while preserving original formatting.

## Core Pattern

```python
import docx
doc = docx.Document('path/to/input.docx')

for p in doc.paragraphs:
    if 'target string' in p.text:
        # ... modify p
        break

doc.save('path/to/output.docx')
```

## Replace Text While Preserving Formatting

**DON'T** use `p.text = new_text` — this destroys run-level formatting (bold, font size, color).

**DO** use a replace function that reconstructs within the existing runs:

```python
def replace_in_para(para, old_text, new_text):
    full = para.text
    if old_text not in full:
        return False
    
    # Save first run's formatting
    r0 = para.runs[0]
    fmt = dict(
        bold=r0.bold, italic=r0.italic,
        font_name=r0.font.name, font_size=r0.font.size,
    )
    
    new_full = full.replace(old_text, new_text)
    
    # Clear all runs, rewrite first run
    for run in para.runs:
        run.text = ''
    para.runs[0].text = new_full
    
    # Restore formatting
    r0 = para.runs[0]
    if fmt['font_name']: r0.font.name = fmt['font_name']
    if fmt['font_size']: r0.font.size = fmt['font_size']
    if fmt['bold'] is not None: r0.bold = fmt['bold']
    if fmt['italic'] is not None: r0.italic = fmt['italic']
    
    return True
```

## ⚠️ Critical Pitfall: Non-Breaking Spaces (\\xa0)

Microsoft Word inserts `U+00A0` (non-breaking space) between abbreviations and numbers, e.g. "No. 80" becomes `No.\xa080`. This breaks naive string matching:

```python
# BROKEN: "Survey No. 80" won't match "Survey No.\xa080"
if 'Survey No. 80' in p.text:   # False!

# FIXED: Try both variants
variants = [old_text, old_text.replace(' ', '\xa0')]
for v in variants:
    if v in full:
        actual_old = v
        break
```

Always check with `repr(p.text)` to see the actual characters before writing find-and-replace logic.

## Inserting a New Paragraph

Use the `addnext()` method on the XML element:

```python
from docx.oxml import OxmlElement

new_p_elem = OxmlElement('w:p')
r_elem = OxmlElement('w:r')
t_elem = OxmlElement('w:t')
t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
t_elem.text = 'Text content here'
r_elem.append(t_elem)
new_p_elem.append(r_elem)

# Insert AFTER target paragraph
target_para._element.addnext(new_p_elem)
```

## Deleting a Paragraph

```python
def delete_paragraph(paragraph):
    parent = paragraph._element.getparent()
    parent.remove(paragraph._element)

# Find by content and delete
for p in list(doc.paragraphs):
    if p.text.strip() == '7. Validity':
        delete_paragraph(p)
        break
```

**Important:** After any insert/delete, the `doc.paragraphs` list is recalculated — indices shift. Always search by content, not by index. Use `list(doc.paragraphs)` when deleting in a loop to avoid iteration errors.

## Complete Editing Pattern

For multi-edit workflows, **do all edits from bottom to top** (paragraph index–wise) so earlier removals/insertions don't shift indices for later edits. Or better: always search by content, never rely on fixed indices.

```python
# 1. Search by text content (not index)
for p in doc.paragraphs:
    if 'target content' in p.text:
        replace_in_para(p, old, new)
        break

# 2. Insert after a known paragraph
for p in doc.paragraphs:
    if 'anchor text' in p.text:
        p._element.addnext(new_p_element)
        break

# 3. Delete sections
for p in list(doc.paragraphs):
    if p.text.strip() == 'heading to remove':
        delete_paragraph(p)
        break
```

## Environment Notes

- No pip — use `uv run python3` to access python-docx (installed via `uv pip install python-docx`)
  - Create a venv: `cd /opt/data && uv venv && source .venv/bin/activate && uv pip install python-docx`
  - **Critical**: `execute_code()` runs OUTSIDE any venv — it uses its own sandbox with the system python. Always use `terminal()` with `source .venv/bin/activate && python3` for python-docx scripts, NOT `execute_code()`.
  - Alternative: create a reusable temp venv at `/tmp/docx_venv` and source it before every terminal call.
- Always verify edits by re-reading the saved document and printing key paragraphs
- Use `repr()` to see actual text characters (catches \xa0 issues)
- Get **full paragraph text**, not truncated views — print paragraphs in one pass with no character limit to spot all occurrences

## Handling Section Numbering After Insert/Delete

DOCX paragraphs are authored manually — section numbers (1., 2., etc.) are **text in the paragraph**, not auto-numbering. After removing or inserting sections, manually fix the numbering:

```python
# After deleting section 7, renumber section 8 → 7
for p in doc.paragraphs:
    if p.text.strip().startswith('8. '):
        replace_in_para(p, '8. ', '7. ')
```

Best practice: after all insertions/deletions, do a final pass to renumber all heading paragraphs sequentially based on the order they appear in the document.
