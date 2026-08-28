# Editing Google-Docs-Exported .docx (tables, text boxes, content-locked blocks)

Worked example: updating the "2026 DRA - HR POLICY .docx" Standard Deductions table (Aug 2026).
The document was created/exported from Google Docs and downloaded via Drive API as a .docx.

## Core pitfall: python-docx sees ZERO tables when the doc came from Google Docs

Google exports wrap every table cell in content-locked structured document tags:

```
w:sdt > w:sdtPr > (w:lock w:val="contentLocked") + w:tag "goog_rdk_N"
     > w:sdtContent > w:tc > w:p > w:r > w:t
```

python-docx's `doc.tables` only iterates TOP-LEVEL tables, so a Google-exported doc
with real tables reports `len(doc.tables) == 0` even though the tables are present and render fine in Word.

Diagnosis that works:
1. `unzip -o file.docx -d x/` then grep `word/document.xml` for `w:tbl` — count the occurrences
2. Or regex `re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.S)` — this DOES find them
3. Extract cell text with `re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cell)` per `w:tc`

Never conclude "the table is an image / it's tab-separated text" — check the XML first.

## Editing the tables with lxml (not python-docx)

Work directly on the parsed XML, preserving all formatting:

```python
from lxml import etree
import copy
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def q(tag): return f'{{{W}}}{tag}'
tree = etree.parse('x/word/document.xml')
root = tree.getroot()
tbls = root.findall(f'.//{q("tbl")}')          # ALL tables, incl. nested/sdt-wrapped
rows = tbls[0].findall(f'{q("tr")}')
cells = row.findall(f'.//{q("tc")}')            # cells sit under sdt>sdtContent>tc
```

Set a cell's text by keeping the FIRST run's rPr (copy formatting), removing all runs
in the first paragraph, then appending one new run with the text:

```python
def set_cell_text(tc, text):
    p = tc.findall(q('p'))[0]
    runs = p.findall(q('r'))
    rpr_tpl = runs[0].find(q('rPr')) if runs else None
    if rpr_tpl is not None: rpr_tpl = copy.deepcopy(rpr_tpl)
    for r in runs: p.remove(r)
    r = etree.SubElement(p, q('r'))
    if rpr_tpl is not None: r.append(rpr_tpl)
    t = etree.SubElement(r, q('t'))
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = text
```

Inserting a NEW row: `copy.deepcopy(an existing data row's w:tr)` then
`tbl.insert(index, newrow)` — clone-and-modify beats building XML from scratch.

Appending a sentence to an existing paragraph: clone the last run's rPr into a new run,
add `<w:br type="textWrapping"/>` then the text.

Write back with `tree.write(path, xml_declaration=True, encoding='UTF-8', standalone=True)`.

## Rezip pitfall: selective zip breaks the package — ALWAYS rezip the whole dir

First attempt rezipped only `[Content_Types].xml _rels docProps word customXml` and produced
a corrupt file: `KeyError: "There is no item named 'customXML/item1.xml' in the archive"`
when re-opening with python-docx.

Root cause: Google export has BOTH `customXml/` references in rels AND a `customXML/`
directory (case differs!). A selective/glob zip that misses either one breaks the OPC package.

The fix that works every time — from the unzipped directory:
```bash
cd x && zip -r -X ../edited.docx . -x '.*' && cd ..
```
then ALWAYS validate by reopening: `docx.Document('edited.docx')` must not throw.

## Verify before delivering

Re-extract and print every table row after editing — confirm the changed rows AND that
rows you didn't touch are intact (renumbering, stale cross-references like "After 3 Warnings"
can silently break).

## Uploading a companion copy (DRAAS convention: never modify originals)

For documents owned by someone else (e.g. HR/Shireen), upload a COPY with a clear
suffix name (`2026 DRA - HR POLICY (10.30 Buffer Update).docx`) rather than overwriting:

```python
media = MediaFileUpload(local_path,
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)
up = svc.files().create(body={'name': name}, media_body=media,
                        fields='id,name,webViewLink').execute()
```

Mirror the original's permissions — BUT skip the `owner` role:
- `permissions().create(..., body={'type':'user','role':'owner','emailAddress':...})` → 403
  `"The transferOwnership parameter must be enabled when the permission role is 'owner'."`
- Grant everyone else the same role (writer/reader). Owner of the copy = the account that uploaded.

Check which email is already granted (`permissions().list`) before re-granting to avoid
duplicate-permission errors, and verify final perms with a list call.
