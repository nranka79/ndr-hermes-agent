# Expanding title-chain recitals in a .docx deed from OCR'd scanned deeds (yellow-highlight)

DRA Group pattern (Bharat / NDR, verified 2026-08-21, Ranka Oasis absolute sale deed):
a vendor's absolute sale deed (e.g. Sevaganapalli Land Partners selling Plot 119 at Ranka
Oasis) carries a title-chain recital list — "(i) Sale Deed dated ... / (ii) Exchange Deed
dated ... / (iii) Sale Deed dated ...". The user supplies the scanned registered deed PDFs
one at a time (Drive links) and asks to **expand each recital** with the parties and all
survey numbers (with extents) from that deed, **highlighting every addition in yellow** and
re-uploading the SAME .docx in place.

If the task is instead to **swap parties, restructure all recitals, and replace schedules in one pass**, see **Pattern C** below.

Runs one deed at a time — treat each Drive link as one more recital to expand, not a fresh
document. The source deeds are large Adobe-Scan-on-Android PDFs (there is no text layer).

## The data you need from each scanned deed

1. **Parties**: first seller name + "and others" (never list the 100+ co-vendors — user
   explicitly says keep just the first and "and others"); the purchaser firm (often the
   VENDOR named in the NEW deed you're editing).
2. **Survey numbers with extents** from that deed's Schedule of Properties (a table at the
   rear of the deed listing `Survey No.<no>, Dry Ext Hec.0.x (or) Ac.0.y cents, ...`).
3. **Total extent** (e.g. the schedule footer "Item Nos. 1 to 19 altogether making a total
   extent of Ac.7.53 cents").
4. Registered document number + Sub-Registrar office (usually already in the recital being
   edited — keep it).

## OCR pipeline for the scanned deed

- The deed is a scanned PDF (`pdftotext dir.pdf out.txt` → <100 bytes). There is NO text
  layer. Render + OCR, and for a multi-hundred-page deed **don't OCR everything** —
  be surgical:
  - OCR page 1 for the first party (first vendor) and the purchaser.
  - Scanned TN deeds repeat a signature-page-per-vendor pattern — skip those.
  - The property schedule with survey numbers+extents is typically in the last few content
    pages before the signatures, or where the "Schedule of Properties" heading appears in
    the operative clause. Grep OCR output for `schedule|extent|Dry|Hec|Ac\\.` to locate it.
  - Always confirm the purchased-firm name from the deed's own opening text (the vendee
    appears as e.g. "In SEVAGANAPALLI VILLAGE ... VENDEE"), not from a filename.
- For the schedule, render that page at 200–300 DPI and pass the PNG to `vision_analyze`
  to read exact survey numbers + extents (OCR line-mangles the number columns).

## .docx edit — lxml on word/document.xml with w:highlight (NOT python-docx WD_COLOR_INDEX)

**CRITICAL — Google Docs highlighting pitfall (learned 2026-08-21):**
`WD_COLOR_INDEX.YELLOW` in python-docx produces `<w:shd w:fill="yellow">` (paragraph
shading) which Google Docs does NOT render as visible yellow highlighting. Google Docs
only recognises `<w:highlight w:val="yellow">` — the actual text highlighter tool.

Always edit the raw XML via lxml, NOT python-docx. Use
`/opt/data/.venv-docx/bin/python3` (has lxml + python-docx).

### Helper functions (reusable across all patterns):

```python
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NS_XML = '{http://www.w3.org/XML/1998/namespace}space'

def make_hl_run(text, bold=False):
    r = ET.Element(f'{W}r')
    rPr = ET.SubElement(r, f'{W}rPr')
    hl = ET.SubElement(rPr, f'{W}highlight'); hl.set(f'{W}val', 'yellow')
    sz = ET.SubElement(rPr, f'{W}sz'); sz.set(f'{W}val', '22')
    szCs = ET.SubElement(rPr, f'{W}szCs'); szCs.set(f'{W}val', '22')
    if bold:
        ET.SubElement(rPr, f'{W}b'); ET.SubElement(rPr, f'{W}bCs')
    t = ET.Element(f'{W}t'); t.set(NS_XML, 'preserve'); t.text = text
    r.append(t)
    return r

def make_hl_para(text, bold=False):
    p = ET.Element(f'{W}p')
    pPr = ET.SubElement(p, f'{W}pPr')
    ps = ET.SubElement(pPr, f'{W}pStyle'); ps.set(f'{W}val', 'Normal')
    sp = ET.SubElement(pPr, f'{W}spacing')
    sp.set(f'{W}after', '120'); sp.set(f'{W}line', '360'); sp.set(f'{W}lineRule', 'auto')
    p.append(make_hl_run(text, bold=bold))
    return p

def make_empty_para():
    p = ET.Element(f'{W}p')
    pPr = ET.SubElement(p, f'{W}pPr')
    sp = ET.SubElement(pPr, f'{W}spacing')
    sp.set(f'{W}after', '120'); sp.set(f'{W}line', '360'); sp.set(f'{W}lineRule', 'auto')
    return p

def get_para_text(p):
    parts = []
    for t in p.iter(f'{W}t'):
        if t.text: parts.append(t.text)
    return ''.join(parts)
```

### Three patterns:

**Pattern A — Insert NEW paragraphs after the recital (for title-flow / chain-of-title):**
The recital paragraph itself stays as-is. New paragraphs go after it in the XML body.

```python
# Find target paragraph in body children
target_para = paras[IDX]
target_pos = None
for i, child in enumerate(list(body)):
    if child is target_para:
        target_pos = i
        break

# Insert after it
insert_pos = target_pos + 1
for text, is_bold in title_flow_lines:
    if text == "":
        p = ET.Element(f'{W}p')  # empty para
        body.insert(insert_pos, p)
    else:
        p = make_hl_para(text, bold=is_bold)
        body.insert(insert_pos, p)
    insert_pos += 1

# Save + repack
tree.write('/tmp/docx_temp/word/document.xml', xml_declaration=True, encoding='UTF-8')
os.chdir('/tmp/docx_temp')
with zipfile.ZipFile('/tmp/out.docx', 'w', zipfile.ZIP_DEFLATED) as outzip:
    for dirpath, _, filenames in os.walk('.'):
        for fn in filenames:
            outzip.write(os.path.join(dirpath, fn), os.path.relpath(os.path.join(dirpath, fn), '.'))
```

**Pattern B — Rebuild the recital paragraph itself (for expanding the recital text):**
Use python-docx to remove runs and rebuild with `w:highlight` in the raw XML. But
since `WD_COLOR_INDEX` maps to `w:shd` (not `w:highlight`), you must post-process
the XML to replace `w:shd` with `w:highlight`:

```python
# After python-docx save, convert w:shd to w:highlight
for p in root.findall('.//w:p', ns):
    for r in p.findall(f'.//{W}r', ns):
        rPr = r.find(f'{W}rPr')
        if rPr is None:
            continue
        # Remove any existing shd
        for shd in rPr.findall(f'{W}shd'):
            if shd.get(f'{W}fill') == 'yellow':
                rPr.remove(shd)
                # Add w:highlight instead
                hl = ET.SubElement(rPr, f'{W}highlight')
                hl.set(f'{W}val', 'yellow')
```

**Pattern C — Full document restructure: replace parties, all recitals, AND schedules in one pass**

Use when the user asks to swap parties (e.g. VENDOR/Promoter becomes one entity, CONFIRMING PARTY becomes another) AND replace all title-flow recitals AND restructure the Schedule A/B sections — all in a single combined .docx with yellow highlights on every new/changed paragraph.

**Strategy** (Ranka Oasis pattern, verified 2026-08-21):

1. **Map body indices** before any editing. Extract every para text, find landmarks:

   ```python
   all_paras = list(body.iter(f'{W}p'))
   p_texts = [get_para_text(p) for p in all_paras]
   
   def pidx_to_body(pidx):
       count = 0
       for bi, child in enumerate(list(body)):
           if child.tag == f'{W}p':
               if count == pidx: return bi
               count += 1
       return None
   
   b_parties = pidx_to_body(10)       # "BY AND BETWEEN"
   b_now = pidx_to_body(48)           # "NOW THEREFORE THIS AGREEMENT WITNESSETH"
   b_annexure = pidx_to_body(143)     # "ANNEXURE 1" or final section
   ```

2. **Build `new_body` list** in 4 segments:

   - **Segment 1 (unchanged)**: Title, date, "BY AND BETWEEN" — `body[0]` to `body[b_parties]`
   - **Segment 2 (new, highlighted)**: New parties definitions — VENDOR, CONFIRMING PARTY, ALLOTTEE
   - **Segment 3 (new, highlighted)**: Complete Section A replacement — GROUP 1 through GROUP N recitals + Consolidation recital + restructured Schedule A/B/C
   - **Segment 4 (unchanged)**: NOW THEREFORE through ANNEXURE through end — every original operative clause, IN WITNESS WHEREOF, ANNEXURE, signatures

3. **Remove original Schedule A/B sections** — they live between IN WITNESS WHEREOF and ANNEXURE. Map them by their body indices and skip them from Segment 4.

4. **Editorial constraint**: The operative clauses still refer to "Promoter" and "Co-Promoter" because those are contractual definitions embedded in the clauses. Do NOT change those — only change the parties DEFINITION section and the WHEREAS recitals.

5. **Write back**: Replace all body children at once — `body.remove(child)` for every child, then `body.append(child)` for each entry in new_body. Preserve any non-`w:p` trailing element (usually `w:sectPr`).

**Ranka Oasis Agreement for Sale — known body index map:**

| Landmark | Para Index | Body Index |
|----------|-----------|------------|
| "AGREEMENT FOR SALE" title | para[7] | body[7] |
| "BY AND BETWEEN" | para[10] | body[10] |
| First WHEREAS | para[28] | body[28] |
| "NOW THEREFORE THIS AGREEMENT WITNESSETH" | para[48] | body[48] |
| "IN WITNESS WHEREOF parties hereinabove" | para[105] | body[105] |
| "SCHEDULE A - DESCRIPTION OF THE TOTAL LAND" | para[111] | body[111] |
| "SCHEDULE B - DESCRIPTION OF THE PLOT" | para[120] | body[120] |
| "ANNEXURE 1- SCHEDULE OF PAYMENT" | para[143] | body[143] |
| "Total Sale Consideration" | para[145] | body[145] |
| Final "IN WITNESS WHEREOF" (signatures) | para[148+] | body[148+] |
| `w:sectPr` (trailing non-para) | N/A | body[176] |

To discover these for a NEW template: iterate body_children with `i, child`, check `child.tag == '{W}p'`, and grep `get_para_text(child)` for landmarks.

**Example output structure for verification:**
```
P11: [HL] VENDOR:                            # ← highlighted new section
P12: [HL] M/s. DRA REALTY PRIVATE LIMITED...
P94: NOW THEREFORE THIS AGREEMENT...         # ← no highlight, original preserved
P152: ANNEXURE 1- SCHEDULE OF PAYMENT        # ← no highlight, original preserved
```

**Common pitfalls with Pattern C:**

- **Duplicate Schedule A/B**: The original document has Schedule A/B after IN WITNESS WHEREOF. If you add NEW Schedule A/B in the recital section but DON'T remove the originals, you get duplicate schedules. Solution: start Segment 4 at `b_now` (body[48]), skip `b_sched_a` through `b_annexure - 1`.
- **ALLOTTEE/PURCHASER**: Keep this without yellow highlight if the user only changed the seller side, not the buyer.
- **The `make_hl_run` function needs `w:bCs` and `w:szCs` for bold** — without these, bold text may not render correctly in some word processors.

**PITFALL — tuple unpacking order:** if you build `runs_new.append(("plain", text))`
  and then unpack `for txt, hl in runs_new`, you get `txt="plain"` (written literally) and
  `hl="<text>"` (truthy → EVERYTHING yellow). Keep the tuple `(text, highlight_bool)` and
  unpack as `(txt, hl)`. Verify after: every run shows `hl=YELLOW` and para text reads
  correctly, not a string of "plainhlhlhl...".
- `\\n` inside an `add_run` text creates a paragraph break in some renderers — for a
  Schedule A / Schedule B block, prefer putting each line in its own run (avoid literal
  `\\n` unless you want a hard break; the PDF render converted them to `; `-joined runs).

## Title-flow expansion (chain-of-title per survey number)

The user may ask for a **full title chain** after each recital, showing how each survey
number came to the vendor and then to the vendee. This is a multi-paragraph block inserted
right after the recital, all highlighted yellow.

The title flow is extracted from the **recitals/whereas clauses** of the scanned deed, which
trace the chain of ownership (ancestral → partition → gift → sale → GPA → final sale).
Structure:

```
The title flow of the VENDOR in respect of the survey numbers comprised in the
said [Deed type] dated [date] (Document No.XXXX/2024) is summarized as under:

[Schedule 'A' / vendor group heading — bold]
[blank line]
[Survey number — bold label line]
[Chain text — colon-separated flow from original owner through to the vendor]
[blank line]
[Survey number — bold label line]
[Chain text]
...
[blank line]
Thus [vendor] acquired title to [extent] in [survey numbers] and conveyed to
[the vendee] under the [Deed type].
```

- **Schedule headings** are bold + yellow highlighted
- **Survey number labels** are bold + yellow highlighted
- **Chain text** is regular weight + yellow highlighted
- **Blank lines** between each survey number for readability
- The chain ends with a concluding "Thus..." paragraph

Each survey number's chain is a single paragraph:

```
Originally belonged to [person] (Patta No.X). [Person] sold to [next person]
(Sale deed dd.mm.yyyy, Doc.XXXX/YYYY). [...] After [person's] death,
succeeded by [legal heir]. By Partition deed dd.mm.yyyy (Doc.XXXX/YYYY),
allotted to [vendor]. [Vendor] sold to [vendee/purchaser] (Sale deed dd.mm.yyyy,
Doc.XXXX/YYYY SRO Hosur).
```

## Inserting a new recital mid-list (renumbering subsequent recitals)

When the user supplies a deed for a new sub-clause that goes between existing ones
(e.g. new recital (iv) when (iv)-(vi) already exist), you must:

1. **Renumber the existing recital paragraphs** by finding each `(iv)` → `(v)`, `(v)` → `(vi)`,
   `(vi)` → `(vii)` in the XML text runs.
2. **Insert the new recital paragraph** at the correct position (after the last title-flow
   paragraph of the preceding recital).
3. **Add the title-flow paragraphs** right after the new recital text.
4. Verify the sequence is correct: (iii) → title flow → (iv) → title flow → (v) → (vi) → (vii).

## Verify + re-upload in place

1. Re-download the .docx from Drive and verify by reading `word/document.xml` — check
   that every paragraph in the inserted range has `<w:highlight w:val="yellow">` on its
   runs, and that any renumbering was applied correctly.
2. Re-upload in place: `drive.files().update(fileId=<same id>, media_body=MediaFileUpload(...))`.
   Same file ID = same link/share preserved.
3. **Do NOT use Drive export-to-PDF for verification** — the file is a .docx (not a Google
   Doc), so `files().export(mimeType='application/pdf')` returns `HttpError 403: Export
   only supports Docs Editors files`. Instead, re-download and check the XML.
4. For local edits (not Drive re-upload): verify via `zipfile` + `ET.fromstring` check of
   paragraph count and highlight presence counts before delivering to the user.

## Confer with the user before this is a "class" — recap what was done

Present the extracted parties + the full survey-number list (with extents and total) in the
reply so the user can spot a spelling/number discrepancy (e.g. "Sabina Palli" vs the deed's
"Sevaganapalli") before it's baked in.