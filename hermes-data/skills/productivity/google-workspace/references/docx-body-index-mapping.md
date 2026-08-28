# .docx Body Index Mapping — Finding landmarks in word/document.xml

When editing a .docx via lxml on `word/document.xml`, you need to find where sections live
by **body child index**, not Python list index. The body can contain non-`w:p` elements
(`w:sectPr`, `w:tbl`, etc.) that shift the mapping.

## The mapping method

```python
import zipfile, xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

with zipfile.ZipFile('document.docx') as z:
    root = ET.fromstring(z.read('word/document.xml'))

body = root.find(f'.//{W}body')
body_children = list(body)

def get_para_text(p):
    parts = []
    for t in p.iter(f'{W}t'):
        if t.text: parts.append(t.text)
    return ''.join(parts)

def pidx_to_body(pidx, body_children):
    """Convert 'Nth paragraph in the document' to body child index."""
    count = 0
    for bi, child in enumerate(body_children):
        if child.tag == f'{W}p':
            if count == pidx: return bi
            count += 1
    return None

# Print all paragraphs with their body index
for bi, child in enumerate(body_children):
    if child.tag == f'{W}p':
        text = get_para_text(child)
        if text.strip():
            print(f"body[{bi}]: {text[:120]}")
    else:
        print(f"body[{bi}]: <{child.tag.split('}')[1]}> (non-para)")
```

## Key landmarks to search for

| What to find | Search text |
|---|---|
| Parties start | "BY AND BETWEEN" |
| WHEREAS start | "WHEREAS" |
| Operative clause start | "NOW THEREFORE" |
| Recital numbering | "(i)", "(ii)", "(iii)", etc. |
| IN WITNESS clause | "IN WITNESS WHEREOF" |
| Schedule A start | "SCHEDULE A" |
| Schedule B start | "SCHEDULE B" |
| Annexure start | "ANNEXURE" or "SCHEDULE OF PAYMENT" |
| Signatures | "IN WITNESS WHEREOF" (second occurrence, near end) |
| Trailing non-para | Check last child; if not `w:p`, it's `w:sectPr` |

## Common template structure

Most Indian real estate Agreement for Sale .docx files follow this layout:

1. **Title** (1 para) — "AGREEMENT FOR SALE" / "SALE DEED"
2. **Date & place** (1 para)
3. **Parties section**: "BY AND BETWEEN" + 3-12 party definition paragraphs
4. **WHEREAS recitals** (lettered A-I or numbered 1-8)
5. **"NOW THEREFORE THIS AGREEMENT WITNESSETH"**
6. **Operative clauses** (numbered 1-21)
7. **"IN WITNESS WHEREOF"** (between operative clauses and schedules)
8. **Schedule A** + Schedule B + optional Schedule C
9. **"ANNEXURE 1"** / payment schedule
10. **Final "IN WITNESS WHEREOF"** (signatures block)
11. **`w:sectPr`** (always last, non-para element)

## Pitfall: para index vs body index

`list(body.iter(f'{W}p'))` returns ALL `w:p` elements in tree order — every nested paragraph
inside tables, headers, etc. This count differs from `list(body)` children.

Use `pidx_to_body()` to map between them, or iterate `body_children` directly with
`if child.tag == f'{W}p'` to skip non-paragraph elements.

## Pitfall: duplicate landmarks

"IN WITNESS WHEREOF" appears TWICE: once as the formal closing before Schedules (body ~105)
and once as the signature block header near the end (body ~148+). Disambiguate by checking
what text follows or by index range (first occurrence is earlier).