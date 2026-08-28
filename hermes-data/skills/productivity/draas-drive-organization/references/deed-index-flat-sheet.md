# Flat Deed Index Sheet (Sale Deeds / ATS / GPA across all survey folders)

When the user wants ONE additional sheet listing all title documents (sale deeds, ATS, GPA)
across a whole land-document Drive folder — as opposed to the per-survey sheets in
`folder-index-spreadsheet.md`. Trigger: "add a sheet with all the sale deeds / ats / gpa
with links from 2012 onwards", often with party references (Sanchaya, Ramesh Reddy, Mahesh,
Shivappa Reddy, etc.).

## 1. Locate the target spreadsheet (fresh sessions)

"the above spreadsheet" in a new session = find it via session_search (spreadsheet name +
session title) AND Drive query
`mimeType='application/vnd.google-apps.spreadsheet' and modifiedTime > '<recent>'`.
Duplicate files with the same name created minutes apart are common (an aborted first build
+ the delivered one). Pick the one actually DELIVERED in the prior session (check session
history for the link), verify `files().get(fields='owners')` shows the requesting user.

## 2. Walk the folder tree

Same parallel BFS + thread-local services as `folder-index-spreadsheet.md`. Save every file
with id/name/path/modifiedTime to JSON before building anything.

## 3. Classify by filename (regex, case-insensitive)

```python
def classify(name):
    n = name.lower()
    if 'thumbs' in n or '.onetoc2' in n: return None
    if re.search(r'\bsale\s*deed\b|\bsale\s*dee\b|\bsald deed\b|\bsale-deed\b', n) \
       or re.match(r'^sale\b', n) or 'sale doc' in n:
        return 'SALE DEED'
    if re.search(r'\bats\b', n): return 'ATS'
    if re.search(r'\bgpa\b|\bgeneral power of attorney\b', n): return 'GPA'
    if 'sanchaya' in n and re.search(r'\bs\.?\s?d\.?\b', n): return 'SALE DEED'
    if re.search(r'\bdeed\b|\bpartition\b|\bmortgage\b|\bmortagage\b', n): return 'DEED'
    return None
```

## 4. Parse doc number + fiscal year — CENTURY HEURISTIC (critical)

Filenames embed doc number + fiscal year: `Doc no 1962-13-14`, `Sale 4313-09-10`,
`ATS 946-11-12`, `SALE DEED - Sanchaya-DOC- NO -1652-12-13`.

```python
m = re.search(r'(?:doc\s*(?:no|number)?\.?\s*)?(\d{2,5})\s*-\s*(\d{2})\s*-\s*(\d{2})', name, re.I)
def century(yy):           # 92-93 → 1992, 13-14 → 2013
    y = int(yy)
    return 1900 + y if y >= 40 else 2000 + y
```

**Without the >=40 rule, "Deed 3176-92-93" parses as 2092-2093 and "775-76-77" as
2076-2077**, polluting any "2012 onwards" filter with nonsense decades. Always sanity-check
the year distribution after parsing (2012-13, 2013-14, 2014-15 clusters look right; 20xx-21xx
values mean the heuristic is missing).

## 5. Party / reference extraction

Filename tokens: `sanchaya` → Sanchaya, `\bpk\b` → PK, `mahesh` → Mahesh, `shivappa|shiv` →
Shivappa, `ramesh` → Ramesh, `nahar` → Nahar. 21+ Sanchaya sale deeds pattern in
Bestamanahalli: doc numbers 1652-12-13 … 4719-14-15.

**Parties named by the user may live in OTHER project folders** — e.g. "RameshDRA Reddy"
GPA/JDA files found on Drive belong to Sevaganapalli / Ranka Oasis, not Bestamanahalli.
Do NOT silently mix different projects into the sheet; flag and ask whether to add a
separate tab.

## 6. Scanned PDFs (pdftotext empty)

Newly uploaded deed scans have no text layer. Render page 1 and OCR:
`pdftoppm -f 1 -l 1 -r 150 -png file.pdf /tmp/pg` then `vision_analyze` on the PNG.
This identifies GPA cover pages (parties, CIN/PAN, doc page count) and survey-list sheets
("BESTHYAMANALLI SY NO MAHESHANNA", "PAVANCHAND NAHAR GPA") that are otherwise opaque.

## 7. Sheet layout

Columns: Sl No / Doc Type / Doc No / Year / Survey No / Party / File Name / Drive Link /
Date (Drive modified). Links: `https://drive.google.com/file/d/<ID>/view`.

Sections (tinted via repeatCell):
- top rows (gold): latest reference docs — 2026 GPA + survey lists
- middle: parsed FY >= 2012 rows sorted year desc
- bottom (grey): files with no year in the filename — NEVER drop these; they are the
  numbered scan batches of the same title chain ("7 Sy138 Sale Deed.pdf")
  and may predate/antedate the parsed set. Mark Year as "n/a (not in filename)".

## 8. Formatting pitfall — Google Sheets API

`foregroundColor` (e.g. white header text) is NOT a top-level field of
`userEnteredFormat`. It must be nested inside `textFormat`:

```python
{'userEnteredFormat': {
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'backgroundColor': {'red': 0.15, 'green': 0.2, 'blue': 0.35}}}
```

Top-level placement → HttpError 400 "Unknown name foregroundColor at
'requests[0].repeat_cell.cell.user_entered_format'". Values + addSheet succeed first, so
the failure shows up only in the formatting batch — run formatting in a separate call and
expect this.

## 9. Verify after writing

Read back header + first/last rows; count by type (SALE DEED / ATS / GPA / DEED); confirm
every data row carries a valid `drive.google.com/file/d/` link; confirm owner is the
requesting user. Report counts + party breakdown in the delivery message.
