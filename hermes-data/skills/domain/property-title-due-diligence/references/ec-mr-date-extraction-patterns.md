# EC & MR Date/Number Extraction Patterns

## EC Date Ranges — From Original Filenames

Encumbrance Certificate filenames encode the search period as a date range in **DDMMYYYY** format.

### Pattern: `DDMMYYYY to DDMMYYYY`

```
01042004 To 10032026 EC SyNo 274.pdf
         ↓               ↓
2004-04-01         2026-03-10
```

### Conversion Function

```python
def parse_ddmmyyyy(d):
    """Convert DDMMYYYY to YYYY-MM-DD."""
    if len(d) == 8 and d.isdigit():
        return f"{d[4:8]}-{d[2:4]}-{d[0:2]}"
    return ''

# Extract from original filename ONLY (never from already-renamed name)
m = re.search(r'(\d{8})\s*[Tt][Oo]\s*(\d{8})', original_filename)
if m:
    d1 = parse_ddmmyyyy(m.group(1))
    d2 = parse_ddmmyyyy(m.group(2))
    if d1 and d2 and d1.startswith(('19','20')) and d2.startswith(('19','20')):
        date_range = f"{d1} to {d2}"
```

### ⚠️ CRITICAL PITFALL — Only Run on Original Names

The regex `(\d{8})\s*[Tt][Oo]\s*(\d{8})` will ALSO match date strings in **already-renamed** filenames like:

```
2004-04-01 to 2023-08-11, Sy 302, Lakshmipura, EC.pdf
```

It extracts `20040401` and `20230811`, then `parse_ddmmyyyy()` produces `0104-20-04` and `1108-23-20` — completely corrupted dates.

**ALWAYS** run EC date range extraction on the original filename from the inventory, NEVER on the current Drive filename.

### Alternative Pattern: `YYYYMMDD to YYYYMMDD`

Some filenames use continuous-digit dates:

```
20040401 to 20220729 EC sy no 302.pdf
```

For these, extract directly (no DDMMYYYY conversion needed):
```python
m = re.search(r'(\d{4})(\d{2})(\d{2})\s*[Tt][Oo]\s*(\d{4})(\d{2})(\d{2})', orig)
if m:
    d1 = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    d2 = f"{m.group(4)}-{m.group(5)}-{m.group(6)}"
```

## MR (Mutation Register) Numbers — From Original Filenames

### Year Range Extraction

Original filenames have year ranges in one of these formats:

| Format | Example | Regex |
|--------|---------|-------|
| `YYYY-YYYY` | `2006-2007 MR no 17 sy no 87.pdf` | `\b(\d{4})[-\s](\d{4})\b` |
| `YYYY-YY` | `2021-22 MR No.H49 sy no 87.pdf` | `\b(\d{4})\s*-\s*(\d{2})\b` → reconstruct full year: `m.group(1)[:2] + m.group(2)` |

```python
# Extract year range
yr = ''
m = re.search(r'\b(\d{4})[-\s](\d{4})\b', orig)  # "2006-2007"
if m:
    yr = f"{m.group(1)}-{m.group(2)}"
else:
    m = re.search(r'\b(\d{4})\s*-\s*(\d{2})\b', orig)  # "2006-07"
    if m:
        yr = f"{m.group(1)}-{m.group(1)[:2]}{m.group(2)}"
```

### MR Number Extraction

| Pattern | Example | Extracted Value |
|---------|---------|-----------------|
| `MR no XX` | `MR no 17` | `MR-17` |
| `MR No. HXX` | `MR No. H49` | `MR-H49` |
| `M.R.No. XX` | `M.R.No. 14` | `MR-14` |
| `MR XX/YYYY` | `MR 28/2000-01` | `MR-28` |
| `MR TXX` | `MR T31` | `MR-T31` |

```python
m = re.search(r'(?:MR|M\.?R\.?)\s*(?:No\.?|no\.?)?\s*[:.]?\s*([A-Za-z0-9/]+)', orig)
if m:
    v = m.group(1).strip().rstrip('.')
    v = re.sub(r'[^A-Za-z0-9]', '', v)
    if v and len(v) < 10:
        mr_num = f'MR-{v.upper()}'  # e.g. MR-17, MR-H49, MR-T31, MR-2HC6
```

### ⚠️ PITFALL — Regex Matches RMN Numbers

The pattern `(\d{4})[-\s](\d{2})` also matches RMN numbers like `RMN-1-02883-2011` where `02883-20` triggers a false positive. Always:

1. Check that the matched number is a plausible year range (start year 1990-2030, end year ≈ start+1)
2. Or better: ONLY run MR extraction on filenames that explicitly contain `MR` or `M.R.` or `mutation`
3. NEVER run year-range regex on Sale Deed, GPA, or RMN-bearing filenames

### Safe MR filename assembly

```python
mr = 'MR'  # fallback
if mr_num:
    mr = mr_num

prefix = yr if yr else 'NoDate'
new_name = f"{prefix}, Sy {sy}, {village}, {mr}.pdf"
```

### Examples

| Original Name | New Name |
|---------------|----------|
| `2006-2007 MR no 17 sy no 87.pdf` | `2006-2007, Sy 87, Bomvachanahalli, MR-17.pdf` |
| `2021-2022 MR No.H49 sy no 87.pdf` | `2021-2022, Sy 87, Bomvachanahalli, MR-H49.pdf` |
| `2019-2020 MR no T18 sy no 87.pdf` | `2019-2020, Sy 87, Bomvachanahalli, MR-T18.pdf` |
| `2004-2005 MR no 24 sy no 87.pdf` | `2004-2005, Sy 87, Bomvachanahalli, MR-24.pdf` |
| `2016-11-05, Sy 302, Lakshmipura, MR-H13.pdf` | `2016-11-05, Sy 302, Lakshmipura, MR-H13.pdf` (no year range in original — keep upload date) |

## RMN-Based Cross-Folder Duplicate Detection

Two files with the **same RMN number** are ALWAYS the same registered document, even if they appear in different Sy No folders.

### Detection

```python
from collections import defaultdict

rmn_map = defaultdict(list)
for f in all_files_on_drive:
    for m in re.findall(r'RMN[-\s]?\d+(?:[/-]\d+)?', f['name'], re.IGNORECASE):
        rmn_map[m.upper().replace(' ', '')].append(f)

# Report cross-folder matches
for rmn, files in rmn_map.items():
    if len(files) > 1:
        sy_nos = set()
        for f in files:
            m = re.search(r'Sy\s*(\d+(?:/\d+)?)', f['name'])
            if m: sy_nos.add(m.group(1))
        if len(sy_nos) > 1:
            print(f"RMN {rmn} spans Sy Nos: {', '.join(sorted(sy_nos))}")
```

### Handling

- **Same RMN in different Sy No folders** → The SAME document, not two separate docs. List in both Sy No tabs but flag Remarks: `DUPLICATE - also filed in Sy No X`
- **Same RMN + same size in same folder** → True duplicate. Rename one as `(DUPLICATE COPY)`
- **Do NOT deduplicate across Sy Nos** — cross-Sy-No RMN matches are legitimate references (the document schedule covers multiple properties)

## Name Normalization After Multiple Rename Passes

After running rename more than once, sweep for artifacts:

```python
# 1. Fix SyXXX -> Sy XXX (missing space)
new = re.sub(r'\bSy(\d+)', r'Sy \1', name)

# 2. Fix double RMN: "RMN-1-04889-2020. RMN-1-04889-2020-21"
new = re.sub(r', (RMN[^,]+)\. (RMN\1)', r', \1', new)

# 3. Fix trailing dot before extension
new = re.sub(r'\s+\.pdf', '.pdf', new)

# 4. Fix hyphens that should be slashes in sub-divisions
new = name.replace('Sy 87-3', 'Sy 87/3')
```
