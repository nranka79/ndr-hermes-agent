# Survey-wise Land Document Organization — Ramanagar Project Worked Example

## Source Session
- **User:** Prakash Singh (psingh@draas.com, TG: [REDACTED-TID])
- **Drive Folder:** Ramanagar Land — Magadi Road (120 Acres)
- **Date:** June 2026
- **Scale:** 558 files across 21 survey numbers

## Folder Structure Created

```
Ramanagar Land (root)
├── Sy No 34 — Lakshmipura
├── Sy No 87 — Bomvachanahalli
├── Sy No 87/3 — Bomvachanahalli
├── Sy No 87/12 — Bomvachanahalli
├── Sy No 103 — Lakshmipura
├── Sy No 103/7 — Lakshmipura
├── Sy No 103/11 — Lakshmipura
├── Sy No 103/12 — Lakshmipura
├── Sy No 104 — Lakshmipura
├── Sy No 105 — Lakshmipura
├── Sy No 106 — Lakshmipura
├── Sy No 107 — Lakshmipura
├── Sy No 108 — Lakshmipura
├── Sy No 109 — Lakshmipura
├── Sy No 110 — Lakshmipura
├── Sy No 111 — Lakshmipura
├── Sy No 112 — Lakshmipura
├── Sy No 130 — Lakshmipura
├── Sy No 274 — Bomvachanahalli
├── Sy No 291 — Bomvachanahalli
├── Sy No 302 — Lakshmipura
├── Property Pics and Videos
├── Ramanagar_Legal_Docs_Master_v9 (Google Sheet)
└── (other project-level files)
```

## Initial Folder State (Before Reorganization)

**Already organized folders:**
- `87` (63 files) → renamed to `Sy No 87`
- `103/7` (20 files) → renamed to `Sy No 103/7`
- `103/11` (26 files) → renamed to `Sy No 103/11`
- `103/12` (19 files) → renamed to `Sy No 103/12`
- `Sy No 87/3` (34 files) — already had prefix
- `Sy No 87/12` (21 files) — already had prefix
- `Sy No 274` (12 files)
- `Sy No 291` (16 files)
- `Sy No 302` (23 files)

**Unsorted buckets:**
- `Scanned Documents of Survey Nos wise` (55 files) — named like `103_5.pdf`, `87_1.pdf`, `34_1.pdf`
- `Scanned Documents for Index` (226 files) — named descriptively e.g., `Sy No 103 Form 7 dated 17.11.1997.pdf`
- Root level (31 files) — survey sketches, master sheet, miscellaneous PDFs

**Missing folders created:** Sy No 34, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 130

## File Classification Rules Used

See the regex patterns in SKILL.md §7.2. Key insight: Indian land document filenames almost always contain the Sy No explicitly (`Sy No 87`, `sy no 103`, `SyNo 302`) or implicitly as a leading number prefix (`103_5.pdf`).

## Registration Number Extraction (NEW from this session)

**MR (Mutation Register) numbers** are embedded in original filenames and MUST be extracted BEFORE rename:

| Original Filename | MR Number | Normalized |
|---|---|---|
| `2006-2007 MR no 17 sy no 87.pdf` | MR 17 | `MR-17` |
| `2020-11-04 MR H34 Sy No 302.pdf` | MR H34 | `MR-H34` |
| `2017-06-02 MR T31` | MR T31 | `MR-T31` |
| `2016-11-05 MR H13.pdf` | MR H13 | `MR-H13` |
| `2024-10-22 MR H24` | MR H24 | `MR-H24` |
| `2019-2020 MR no T18 sy no 87.pdf` | MR T18 | `MR-T18` |
| `2021-2022 MR no H49 sy no 87.pdf` | MR H49 | `MR-H49` |
| `2004-2005 MR no 24 sy no 87.pdf` | MR 24 | `MR-24` |

**EC (Encumbrance Certificate) date ranges** in DDMMYYYY format:

| Original Filename | Date Range | Normalized |
|---|---|---|
| `01042004 To 10032026 EC SyNo 274.pdf` | 01/04/2004 to 10/03/2026 | `2004-04-01 to 2026-03-10` |
| `01042004 To 11082023 EC SyNo 302.pdf` | 01/04/2004 to 11/08/2023 | `2004-04-01 to 2023-08-11` |
| `01042004 To 07292022 EC SyNo 302.pdf` | 01/04/2004 to 29/07/2022 | `2004-04-01 to 2022-07-29` |
| `20040401 to 20220331 EC sy 103_11.pdf` | 01/04/2004 to 31/03/2022 | `2004-04-01 to 2022-03-31` |

**Sale Deed / GPA Registration Numbers (RMN):**

| Original Filename | RMN Number |
|---|---|
| `20230310 Sale Deed No. RMN-1-12479-2022-23` | RMN-1-12479-2022 |
| `20081112 GPA No RMN-4-00216-2008-09 Sy No 103-11.pdf` | RMN-4-00216-2008-09 |
| `20110730 Sale Deed No. RMN-1-02883-2011-12` | RMN-1-02883-2011 |
| `20201104 sale deed no 4889(20-21) sy no 302.pdf` | RMN-1-04889-2020 |

**⚠️ Critical — Run extraction on ORIGINAL filenames only:** The DDMMYYYY regex used for EC date ranges will also match ALREADY-RENAMED filenames like `2004-04-01 to 2023-08-11.pdf` by extracting `20040401` and `20230811` and then re-parsing them through `parse_ddmmyyyy()` — which produces corrupted results like `0104-20-04`. Always extract from the pre-rename inventory (original name), never from the current Drive name.

## Master Sheet Structure (Category-Grouped Format)

The per-Sy No tabs group documents by the 8 required document categories (A–H) with sub-headings, sorted oldest→newest within each category.

### Per-Sy No Tab Structure

```
Row 1:  Survey No: 87 — Village: Bomvachanahalli — Total Files: 111
Row 2:  #  |  Document Name  |  Date  |  Category Match  |  Reg No  |  Drive Link  |  Size  |  Remarks
Row 3:  A. Title Documents                                                     ← category header (single cell)
Row 4:    >> Grants / Title Deeds / Deeds (Form 1 to 7)                       ← sub-heading (single cell)
Row 5:  1  |  ❌ RTC — NOT AVAILABLE                                           ← gap: missing required doc
Row 6:  2  |  Sy No 87 Form 1 dated 19.5.1938.pdf                             ← available doc
⋮
Row N:    >> GPA & Authorizations
Row N+1: ...
Row M:    >> Other Documents (this category)                                  ← within-category unclassified
⋮
Row Z:  Other / Unclassified Documents                                        ← global unclassified
```

### Sub-heading Structure

```
A. Title Documents
   >> Grants / Title Deeds / Deeds (Form 1 to 7)  → items 3 (Grant/Form1), 2 (Form7A), 4 (PTCL), 1 (RTC), 5 (Sale Deed)
   >> GPA & Authorizations                         → item 6
   >> Legal Heir / Succession                      → item 7
   >> Other Documents (this category)
B. Revenue Records
   >> Mutation Register (MR)                       → item 8
   >> Encumbrance Certificate (EC)                 → item 9
   >> Index of Land & Classification               → items 10, 11
C. Tahsildar Endorsements
   >> Possession & Identity                        → items 12, 13
   >> Clearances & NOCs                            → items 14, 15, 16, 17
D. Survey & Boundary
   >> Maps & Atlas                                 → items 18, 22
   >> Field Measurement Books                      → items 19, 20, 23, 21, 24
E–H: Single sub-headings each
```

### Data Generation Pattern (Python)

```python
structure = [
    ('A', 'Title Documents', [
        ('Grants / Title Deeds / Deeds (Form 1 to 7)', [3, 2, 4, 1, 5]),
        ('GPA & Authorizations', [6]),
        ('Legal Heir / Succession', [7]),
    ]),
    ('B', 'Revenue Records', [
        ('Mutation Register (MR)', [8]),
        ('Encumbrance Certificate (EC)', [9]),
        ('Index of Land & Classification', [10, 11]),
    ]),
    ...
]

for sy in sy_order:
    # Clear before write
    sheets.spreadsheets().values().clear(...)
    time.sleep(0.5)
    
    rows = [
        [f'Survey No: {sy} — Village: {village} — Total Files: {len(files)}'],
        HEADERS
    ]
    
    for let, main_cat, sub_groups in structure:
        rows.append([f'{let}. {main_cat}'])              # main header (1 cell)
        for sub_name, req_nums in sub_groups:
            rows.append([f'  >> {sub_name}'])            # sub-heading (1 cell)
            for rnum in req_nums:
                if matching_files_exist:
                    rows.append([seq, name, date, label, reg, link, size, ''])
                else:
                    rows.append([seq, f'MISSING: {label}', '', '', '', '', '', ''])
    
    sheets.spreadsheets().values().update(...)
```

## File Renaming Convention

```
YYYY-MM-DD, Sy No, Village, Document Name, Registered Number.ext
```

**Note:** Uses dashes (`-`) not slashes (`/`) in dates. Google Drive filenames cannot contain `/`.

### Rename Execution (515 files)

The rename was executed directly on original files using `drive.files().update(fileId=fid, body={'name': new_name})`. Sheet links remain valid since Drive file IDs don't change on rename.

**New name construction:**

```python
parts = []
parts.append(date_str if date_str else 'NoDate')
parts.append(f'Sy {sy}')
parts.append(village)
parts.append(doc_label)       # e.g. "MR-17", "Sale Deed", "EC Encumbrance Certificate"
if reg_no:
    parts.append(reg_no)      # e.g. "RMN-1-02883-2011"
new_name = ', '.join(parts) + f'.{ext}'
```

### Classification Labeling Examples (from this session)

| New Name | Source Original |
|---|---|
| `2006-2007, Sy 87, Bomvachanahalli, MR-17.pdf` | `2006-2007 MR no 17 sy no 87.pdf` |
| `2020-11-04, Sy 302, Lakshmipura, MR-H34.pdf` | `20201104 MR H34 Sy No 302.pdf` |
| `2004-04-01 to 2026-03-10, Sy 274, Bomvachanahalli, EC.pdf` | `01042004 To 10032026 EC SyNo 274.pdf` |
| `2004-04-01 to 2023-08-11, Sy 302, Lakshmipura, EC.pdf` | `01042004 To 11082023 EC SyNo 302.pdf` |
| `1938-05-19, Sy 87, Bomvachanahalli, Form 1 Grant Title Deed.pdf` | `Sy No 87 Form 1 and Order sheet...dated 19.5.1938.pdf` |
| `2022-10-20, Sy 291, Bomvachanahalli, Agreement of Sale, RMN-1-07017-2022.pdf` | `20221020 Reg Agreement of Sale No. RMN-1-07017-2022-23.pdf` |

### Name Normalization After Multiple Rename Passes

When rename runs more than once, run a normalization sweep:

```python
# Fix SyXXX -> Sy XXX (missing space after Sy)
new = re.sub(r'\bSy(\d+)', r'Sy \1', new)

# Fix double RMN: "RMN-1-04889-2020. RMN-1-04889-2020-21" -> "RMN-1-04889-2020-21"
new = re.sub(r', (RMN[^,]+)\. (RMN\1)', r', \1', new)

# Fix hyphens that should be slashes for sub-divisions
new = f['name'].replace('Sy 87-3', 'Sy 87/3')

# Fix trailing dot before extension
new = re.sub(r'\s+\.pdf', '.pdf', new)
```

## Duplicate Detection Results (this session)

After comprehensive RMN-based + same-size dedup checks:

| Registration Number | Copies | Folders | Result |
|---|---|---|---|
| RMN-1-07017-2022 | 2 | Sy 291, Sy 302 | Cross-Sy-No (legitimate — same agreement covers both SVs). Flagged in sheet |
| RMN-1-04889-2020 | 2 | Sy 302 only | True duplicate (same file, same size 12,494 KB). Renamed as (DUPLICATE COPY) |
| Sy 291: EC at 2430 KB | 2 | Sy 291 only | True duplicate. Renamed as (DUPLICATE COPY) |
| Sy 291: RTC at 15,565 KB | 2 | Sy 291 only | Same RTC docs. Renamed as (DUPLICATE COPY) |
| Sy 291: 662 KB pair | 2 | Sy 291 only | Karda + Tippani — same doc miscatalogued |

**Cross-Sy-No RMN handling:** The same RMN in different Sy No folders is the SAME registered document, NOT a duplicate. An Agreement of Sale or Sale Deed with one RMN covers all properties in its schedule. In the Master Sheet, list the document in BOTH Sy No tabs (relevant to both) but flag Status: `DUPLICATE - also filed in Sy No X`.

## Prakash Working Preferences (Consolidated)

1. **Show sample before bulk operations** — Present concrete sample output + process. Get approval before execution.
2. **Oldest → Newest sort** within each category section
3. **Category sub-headings** — `>> Sub-heading Name` format, single cell per row
4. **Available AND missing listed** — Both present docs and `MISSING: [name]` gaps
5. **Document date, not file timestamp** — Date comes from document content
6. **Cleaned folder approach** — Create SEPARATE "Cleaned" folder with copies. Do NOT modify originals.
7. **Village accuracy** — Confirm village names with domain expert. Accept corrections sharply.
8. **Clear-before-write for sheet tabs** — Prevent stale data artifacts across iterations
9. **Registration numbers from original filenames** — Extract MR, EC date ranges, RMN BEFORE rename
10. **No same document under different names** — Dedup by RMN, file size, and normalized name

## Pitfalls Summary

1. **Drive API timeout** on bulk moves/copies — batch 10-20 per invocation
2. **Sub-division ambiguity** — Cross-reference with known sub-division folders
3. **Timestamp are scan dates, not doc dates** — Need OCR to classify
4. **"Survey No" vs "Sy No"** — Regex must catch both; "Survey" doesn't start with "Sy"
5. **EC date range regex on already-renamed files** — Destructive! Use original names only
6. **MR number extraction overmatching RMN** — Check for explicit MR/M.R. prefix
7. **Village corrections** — Get confirmed before committing to filenames
8. **Clear-before-write** for sheet tabs to prevent stale data
9. **Google Sheets special chars** — Em-dashes cause 400 errors
10. **Same-size files with `(1)` suffix** — Almost always duplicates
