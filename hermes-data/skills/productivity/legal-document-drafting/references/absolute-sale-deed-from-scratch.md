# Building an Absolute Sale Deed from Scratch (lxml / no python-docx)

**When to use this:** No existing .docx to edit. User asks for a complete sale deed from zero. The restructured recitals need to go into a full deed with covenants, flow of title, and schedules.

## Why lxml, not python-docx

| Need | python-docx | lxml |
|------|------------|------|
| Yellow highlight via `w:highlight` | ❌ Uses `WD_COLOR_INDEX.YELLOW` → `w:shd` (invisible in Google Docs) | ✅ Direct `w:highlight w:val="yellow"` |
| Multi-party (VENDOR + CP + VENDEE) | Works but verbose | Full control |
| Section A recital structure | Requires complex XML manipulation | Build exactly what you need |
| Flow of Title numbering | Works | Works |
| All XML boilerplate | Handled | Must create manually |
| Speed for complex docs | Slow (many API wrappers) | Fast |

**Rule:** For any document the user will view in Google Docs, ALWAYS use lxml `w:highlight`, never python-docx `WD_COLOR_INDEX`.

## Directory Structure

```
/tmp/deed_build/
├── [Content_Types].xml
├── _rels/
│   └── .rels
├── word/
│   ├── _rels/
│   │   └── document.xml.rels
│   ├── document.xml
│   └── styles.xml
└── docProps/
    ├── app.xml
    └── core.xml
```

## Step-by-Step Code Pattern

### 1. Namespace constants
```python
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NS_XML = '{http://www.w3.org/XML/1998/namespace}space'
```

### 2. Helper functions (critical — reuse these verbatim)
```python
def make_run(text, bold=False, highlight=False, italic=False):
    r = ET.Element(f'{W}r')
    rPr = ET.SubElement(r, f'{W}rPr')
    if highlight:
        hl = ET.SubElement(rPr, f'{W}highlight'); hl.set(f'{W}val', 'yellow')
    sz = ET.SubElement(rPr, f'{W}sz'); sz.set(f'{W}val', '24')
    szCs = ET.SubElement(rPr, f'{W}szCs'); szCs.set(f'{W}val', '24')
    if bold:
        ET.SubElement(rPr, f'{W}b'); ET.SubElement(rPr, f'{W}bCs')
    if italic:
        ET.SubElement(rPr, f'{W}i'); ET.SubElement(rPr, f'{W}iCs')
    t = ET.Element(f'{W}t'); t.set(NS_XML, 'preserve'); t.text = text
    r.append(t)
    return r

def make_para(runs=[], justify='both', spacing_after=120):
    p = ET.Element(f'{W}p')
    pPr = ET.SubElement(p, f'{W}pPr')
    ps = ET.SubElement(pPr, f'{W}pStyle'); ps.set(f'{W}val', 'Normal')
    if justify:
        jc = ET.SubElement(pPr, f'{W}jc'); jc.set(f'{W}val', justify)
    sp = ET.SubElement(pPr, f'{W}spacing')
    sp.set(f'{W}after', str(spacing_after))
    sp.set(f'{W}line', '360'); sp.set(f'{W}lineRule', 'auto')
    for r in runs: p.append(r)
    return p

def make_text_para(text, bold=False, highlight=False, justify='both', italic=False):
    return make_para([make_run(text, bold=bold, highlight=highlight, italic=italic)], justify=justify)

def make_empty_para():
    p = ET.Element(f'{W}p')
    pPr = ET.SubElement(p, f'{W}pPr')
    sp = ET.SubElement(pPr, f'{W}spacing')
    sp.set(f'{W}after', '120'); sp.set(f'{W}line', '360'); sp.set(f'{W}lineRule', 'auto')
    return p
```

### 3. Build body list
Collect all paragraphs in a Python list:
```python
body_content = []
body_content.append(make_center_para("ABSOLUTE SALE DEED", bold=True))
# ... keep appending every paragraph type in document order
```

### 4. Assemble document.xml
```python
document = ET.Element(f'{W}document')
body_elem = ET.SubElement(document, f'{W}body')
for p in body_content:
    body_elem.append(p)

# Section properties (A4 page)
sectPr = ET.SubElement(body_elem, f'{W}sectPr')
pgSz = ET.SubElement(sectPr, f'{W}pgSz')
pgSz.set(f'{W}w', '11906'); pgSz.set(f'{W}h', '16838')
pgMar = ET.SubElement(sectPr, f'{W}pgMar')
for margin, val in [('top','1134'),('right','1134'),('bottom','1134'),('left','1134')]:
    pgMar.set(f'{W}{margin}', val)

# Write with proper XML declaration
xml_str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(document, encoding='unicode')
with open(f'{TMP}/word/document.xml', 'w', encoding='utf-8') as f:
    f.write(xml_str)
```

### 5. Minimal supporting files

**`[Content_Types].xml`:**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
```

**`_rels/.rels`:**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
```

**`word/_rels/document.xml.rels`:**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
```

**`word/styles.xml`:**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>
  </w:style>
</w:styles>
```

**`docProps/app.xml` and `docProps/core.xml`:** Minimal files declaring application name, title, date.

### 6. Zip everything
```python
os.chdir(TMP)
with zipfile.ZipFile(OUTPUT_PATH, 'w', zipfile.ZIP_DEFLATED) as outzip:
    for dirpath, _, fns in os.walk('.'):
        for fn in fns:
            ap = os.path.relpath(os.path.join(dirpath, fn), '.')
            outzip.write(ap, ap)
```

### 7. Verify
```python
with zipfile.ZipFile(OUTPUT_PATH) as z:
    doc2 = ET.fromstring(z.read('word/document.xml'))
paras = list(doc2.iter(f'{W}p'))
# Check for all required sections
for k in ['ABSOLUTE SALE DEED', 'VENDOR', 'CONFIRMING PARTY', 'VENDEE', 
          'WHEREAS', 'NOW THIS INDENTURE WITNESSETH', 'FLOW OF TITLE',
          'SCHEDULE A', 'SCHEDULE B', 'SCHEDULE C', 'IN WITNESS WHEREOF']:
    found = any(k in t for t in [''.join(t.text or '' for t in p.iter(f'{W}t')) for p in paras])
    assert found, f"Missing section: {k}"
```

## Full Document Structure (in body order)

1. Title: "ABSOLUTE SALE DEED" (center, bold)
2. Preamble: date + place line
3. "BETWEEN" header (center, bold)
4. VENDOR: full legal name, CIN, reg. office, represented by Director name + Board Resolution reference
5. "AND" (center, bold) — repeat for CONFIRMING PARTY if any
6. VENDEE: full name, S/o, age, address, Aadhaar
7. "WHEREAS:" section:
   - Section A recitals (groups 1-N documenting each source deed)
   - Consolidation recital (summary of ownership)
   - 4x "AND WHEREAS" clauses (agreement to sell, consideration paid, possession, encumbrances)
8. "NOW THIS INDENTURE WITNESSETH AS FOLLOWS:" (center, bold)
9. Clause 1: Grant of Sale (with full legal conveyance language + "TO HAVE AND TO HOLD")
10. Clause 2 heading: "covenant, declare and agree" → 13 numbered sub-clauses (i-xiii)
11. "FLOW OF TITLE" (bold) — numbered chain from original owner to vendor
12. SCHEDULE A — project land (all survey numbers)
13. SCHEDULE B — source survey number for the plot
14. SCHEDULE C — the specific plot being conveyed (dimensions, boundaries)
15. "IN WITNESS WHEREOF" (center, bold)
16. Signature blocks: VENDOR, CONFIRMING PARTY, VENDEE
17. Witnesses: 2 witnesses with name, address, signature blanks
18. PLACE and DATE lines

## Pitfalls

- **`ET.tostring` with `standalone=True`**: Python 3.13's lxml does NOT support the `standalone` kwarg. Build the XML declaration string manually:
  `'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(document, encoding='unicode')`
- **`wb` vs `w`**: Write in text mode (`'w', encoding='utf-8'`) for the unicode string from `tostring(..., encoding='unicode')`.
- **Google Docs highlight**: Always `w:highlight w:val="yellow"` on runs. Never `w:shd w:fill="yellow"` on paragraphs. Google Docs ignores `w:shd` as visible formatting.
- **Missing directories**: Create `word/_rels/` and `docProps/` explicitly (they're not created by default).
- **Font size**: `w:sz w:val="24"` = 12pt (half-point units). 24 = 12pt. 22 = 11pt. For headings, use 28-32 (14-16pt) or keep at 24.