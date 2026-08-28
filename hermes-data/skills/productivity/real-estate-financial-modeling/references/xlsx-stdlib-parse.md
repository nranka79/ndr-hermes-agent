# Parsing an xlsx WITHOUT openpyxl (stdlib zipfile + regex)

When openpyxl is unavailable (e.g. execute_code sandbox without the venv, or a
read-only host), an xlsx is just a zip — parse it with stdlib.

## The three files that matter
- `xl/workbook.xml` → sheet names + r:id → rels map
- `xl/_rels/workbook.xml.rels` → r:id → target path
- `xl/sharedStrings.xml` → the actual text (cells with `t="s"` store an INDEX here)
- `xl/worksheets/sheet1.xml` → the grid

## Critical gotcha: shared strings are INDICES, not text
A cell like `<c r="E8" s="11" t="s"><v>6</v></c>` means: E8's text =
`sharedStrings[6]`, NOT the literal "6". A naive regex that grabs `<v>` as the
value produces garbage (this bit the Sreshta intake: first pass returned numbers
like `E8=6` with no text — the real content was in sharedStrings).

Correct resolution:
```python
import zipfile, re, html
z = zipfile.ZipFile(path)
ss = z.read('xl/sharedStrings.xml').decode('utf-8','ignore')
sis = re.findall(r'<si>(.*?)</si>', ss, re.S)
shared = []
for si in sis:
    ts = re.findall(r'<t[^>]*>(.*?)</t>', si, re.S)
    shared.append(html.unescape(''.join(ts)))  # unescape &amp; &lt; etc.

xml = z.read('xl/worksheets/sheet1.xml').decode('utf-8','ignore')
cells = re.findall(r'<c r="([A-Z]+\d+)"([^>]*)>(.*?)</c>', xml, re.S)
grid = {}
for coord, attrs, inner in cells:
    m = re.search(r'<v>(.*?)</v>', inner, re.S)
    if not m: continue
    val = m.group(1)
    t = re.search(r't="(\w+)"', attrs)
    if t and t.group(1) == 's' and val.isdigit() and int(val) < len(shared):
        val = shared[int(val)]
    grid[coord] = val
```

## Other gotchas
- **Merged-cell layouts misalign row printing**: the same cell map can have
  labels in column E and values in G/H/I. Print per-row with column letters
  (`R13: E=86000 sq.ft | F=22000 Sqft | I=Type of land`) and read the
  structure from the row layout, not the raw XML order.
- **`data_only=True` vs raw `<v>`**: raw XML `<v>` is the CACHED value in
  xlsx (no formulas evaluated). That's fine for reading a finished annexure.
- **Filenames from document_cache can contain spaces/&** (e.g.
  `doc_567d17300053_Bang- P& L (1).xlsx` — note the space inside "P& L").
  Copy to a clean `/tmp/name.xlsx` first; shell-quote anything you pass around.
- openpyxl in a venv: `uv pip install --python <venv> openpyxl` if you can
  install — but the stdlib path above is deterministic and dependency-free.
