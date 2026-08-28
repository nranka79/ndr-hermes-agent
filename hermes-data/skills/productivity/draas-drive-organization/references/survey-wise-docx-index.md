# Survey-No.-Wise Document Index from a Drive Folder

When a project folder (e.g. Oasis - print, Byadarahalli Legal) contains 200+ scanned deeds, ECs, Pattas, FMBs, and legal opinions with survey numbers embedded in filenames — produce a **survey-no.-wise Word doc** instead of a flat folder-wise listing.

## When to use

- User says "rearrange list survey-no.-wise" or "group by survey number"
- The folder is a project's document repository with survey numbers, sub-divisions, and P-series parcels
- File names contain survey references in Indian real-estate format: `SyNo.166/3`, `FMB 158(1A2)`, `Patta 167(1A)`, `UDR SY NO 158-1A1A`, etc.

## Survey number extraction — regex patterns

Indian real estate survey numbers appear in many forms. Order of patterns below matches the precedence in the refined extractor:

### Pattern A: Standard SyNo / SY NO / Sy.no / SyNo- (primary)

```
(?:sy[.\s]*no[.\s]*'?s?[:\s\-]*)(\(?\s*[A-Za-z0-9/.\-_]+\s*\)?)
```

Catches: `SyNo.166/1`, `SY NO 158-1A1A`, `Sy.no.158(1A1)`, `SyNo- 166-3F`, `sy no 166/2`, `Sy.No.158_1C9`

Split result by comma/`and` for multi-survey: `Sy No 158(1C3,1C4,1C6,1C9A)` → `158/1C3`, `158/1C4`, `158/1C6`, `158/1C9A`

### Pattern B: FMB + survey number

```
\bFMB\s+(\d+(?:[.\-/(]\d+[A-Za-z0-9]*)*)
```

Catches: `FMB 166-3E1`, `FMB 158 1A1B`, `FMB 158(1A2)`, `FMB 167 1G`

### Pattern C: Patta → survey number (converted)

```
\bPatta\s+(?:no\.?\s*)?(\d+\s*\(?[A-Za-z0-9]*\)?)
```

Catches: `Patta 158(1C3)`, `Patta 167(1A)`, `Patta 166(3D)`, `Patta 167 2C`

Patta numbers without parens (e.g. `Patta 543`, `Patta 1006`) are filtered out — they're page/folio numbers, not survey numbers.

### Pattern D: UDR register references

```
\bUDR[:\s]+(?:SY\s*NO\s+)?(\d+(?:[.\-/\s]\d+[A-Za-z0-9]*)*)
```

Catches: `UDR SY NO 158-1A1A`, `UDR SyNo.158-166-167-168`, `UDR A-Register SyNo.164`

Range separators (`-`) split into individual surveys.

### Pattern E: EC chains with Sy mention

```
\bEC\s.*?\b(?:Sy|SY)[.\s]*[Nn][Oo]?[.\s]*(\d+(?:[._/\-]\d+[A-Za-z0-9]*)*)
```

Catches: `EC 19750401 to 20260812 Sy 177`, `EC from 1960-1986 SyNo.166_3F`

### Pattern F: Adangal with survey number

```
\b[Aa]dangal\b.*?(\d+(?:[._/\-]\d+[A-Za-z0-9]*)+)
```

Catches: `adangal gurramma SyNo- 166-3F`

### Pattern G: sy.no- / syno- trailing (dash format)

```
(?:sy[.\s]*no[.\s]*|syno[.\s]*)[.\-]?\s*(\d+(?:[.\-/\s]\d+[A-Za-z0-9]*)*)
```

Catches: `sy.no-166-3B`, `sy.no-166-3E1,158-1A2`, `syno-177-1A`, `syno-158-1c9B`

### Pattern H: Inline Sy  in text

```
(?:Sy|SY)\s+(\d+(?:[/\-]\d+[A-Za-z0-9]*)*(?:,\s*\d+(?:[/\-]\d+[A-Za-z0-9]*)*)*)
```

Catches: `Munireddy-P.no.581 Sy 166-3A 167-1D,1I`

## Normalization

Convert all survey numbers to a canonical `/` format:

```python
def normalize_survey(s):
    s = s.strip('.()').strip()
    s = re.sub(r'[-_]', '/', s)  # dashes/underscores → slashes
    parts = s.split('/')
    norm = [re.sub(r'^0+(?=\d)', '', p.strip()) for p in parts]
    return '/'.join(norm)
```

Examples:
- `166-3F` → `166/3F`
- `158_1C9` → `158/1C9`
- `158(1A2)` → `158/1A2` (after strip of parens)

## Sorting survey numbers

Natural sort — split on `/`, parse leading integer from each segment:

```python
def sort_key(sn):
    parts = re.split(r'/|\.', sn)
    nums = [int(re.match(r'(\d+)', p).group(1)) if re.match(r'(\d+)', p) else 9999 for p in parts]
    while len(nums) < 3: nums.append(0)
    return tuple(nums)
```

## Deduplication

A single document can map to multiple survey numbers (e.g. a release deed covering `Sy No 157-3,174-2,175-4,176-2`). In the per-survey table, deduplicate: show the doc under each survey, but skip the same doc appearing again under the same survey entry.

## Document date extraction

From filenames, try in order:

1. **8-digit leading prefix** — try YYYYMMDD first, then DDMMYYYY as fallback
2. **"dtd" / "dated" DD[-./]MM[-./]YYYY** — regex match
3. **First-date in EC ranges** — not a reliable document date; leave blank

```python
def extract_date(name):
    n = re.sub(r'^Copy of\s+', '', n, flags=re.I)
    # 8-digit prefix
    m = re.match(r'^(\d{8})(?!\d)', n)
    if m:
        s = m.group(1)
        # Try YYYYMMDD
        y, mo, d = int(s[:4]), int(s[4:6]), int(s[6:8])
        if 1900 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
            return datetime(y, mo, d)
        # Try DDMMYYYY
        dd, mm, yyyy = int(s[:2]), int(s[2:4]), int(s[4:])
        if 1900 <= yyyy <= 2100 and 1 <= mm <= 12 and 1 <= dd <= 31:
            return datetime(yyyy, mm, dd)
    # dtd / dated
    m = re.search(r'(?:dtd\.?|dated?)\s+(\d{1,2})[-./](\d{1,2})[-./](\d{4})', n, re.I)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= d <= 31 and 1 <= mo <= 12 and 1900 <= y <= 2100:
            return datetime(y, mo, d)
    return None
```

## Word document structure

Part 1 — Survey-no.-wise tables (one H2 per survey, one table per survey):
```
# | Date | Document Name | Folder
```

Part 2 — Non-survey documents (by folder, for items with no parseable survey):
```
# | Date | Document Name
```

## Script

A reusable script is at `scripts/survey-wise-index.py`. Run:

```bash
cd /opt/hermes && HERMES_SESSION_USER_ID=psingh \
  /opt/hermes/.venv/bin/python scripts/survey-wise-index.py \
  <FOLDER_ID> <output.docx> [service_name]
```

## References

- `drive-folder-docx-index.md` — simpler per-folder listing (no survey extraction)
- `folder-index-spreadsheet.md` — spreadsheet-based per-category indexing
- `filename-document-table-parsing.md` — structured column parsing from renamed filenames