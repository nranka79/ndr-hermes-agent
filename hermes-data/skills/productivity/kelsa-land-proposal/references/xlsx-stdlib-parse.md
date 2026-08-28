# Reading uploaded .xlsx (P&L annexures, financial workings) with stdlib — no openpyxl needed

openpyxl is often NOT installed on the host (`ModuleNotFoundError`). The stdlib
`zipfile` + regex route is reliable and dependency-free. Two file flavors exist
in the wild — check BOTH:

1. **sharedStrings.xlsx** (most Excel-generated files): cell values live in
   `xl/sharedStrings.xml`; worksheet cells reference them via
   `<c r="E8" t="s"><v>6</v></c>` — the `<v>` is an INDEX into the shared
   string table, NOT the value. **A parse that ignores `t="s"` returns a
   sheet full of small integers / empty cells and looks broken.**
2. **inline-strings.xlsx** (e.g. some Google/partner exports): values sit
   inline in the sheet XML as `<is><t>...</t></is>` — no sharedStrings part.

## Recipe (sharedStrings variant)

```python
import zipfile, re, html

z = zipfile.ZipFile("/tmp/model.xlsx")
# 1. shared string table
ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8', 'ignore')
sis = re.findall(r'<si>(.*?)</si>', ss_xml, re.S)
shared = []
for si in sis:
    ts = re.findall(r'<t[^>]*>(.*?)</t>', si, re.S)
    shared.append(html.unescape(''.join(ts)))

# 2. cells — resolve t="s" indices
xml = z.read('xl/worksheets/sheet1.xml').decode('utf-8', 'ignore')
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
# print grouped by row, cols sorted, skipping empty strings
```

## Pitfalls

- **Worksheet path**: read `xl/workbook.xml` + `xl/_rels/workbook.xml.rels` to
  map sheet names to `xl/worksheets/sheetN.xml` (sheet order ≠ file order).
- **Merged-cell layouts scramble apparent positions** (labels in column J can
  describe the row BELOW, values in E/H are phase columns). Reconstruct
  semantically (labels from shared strings + adjacent numbers) rather than
  trusting cell coordinates.
- **Styled cells look like data**: attrs like `s="9"` are STYLE indexes, not
  values — only `t="s"` means shared-string reference.
- **Verify against the user's words**: after parsing, cross-check numbers
  against what the user narrated (e.g. "86,000 + 22,000 sqft", "₹9-11k/sqft")
  to catch wrong-column reads.

Worked example: `Bang- P&L (1).xlsx` (Sreshta Leisure, Kanakapura Road) —
"SRESHTA LEISURE PVT LTD" developer block, 86k/22k land, 200k/55k built-up,
P&L at ₹9,000/sqft → income ₹153 Cr, cost ₹70.4 Cr, profit ₹75.8 Cr.
