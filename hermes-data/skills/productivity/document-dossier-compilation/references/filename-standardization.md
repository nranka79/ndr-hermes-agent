# Filename Standardization Patterns

When performing a document inventory audit or filename cleanup across Drive folders, the following patterns apply universally regardless of project or person.

## Common filename defects to detect and fix

### 1. Date Format Corrections

| Original Pattern | Example | Fix |
|---|---|---|
| DDMMYYYY | `19082014 NOC issued by fire service.pdf` | `20140819_NOC_issued_by_fire_service.pdf` |
| Corrupted YYYYMMDD | `220241224 Letter of DGP...` (extra leading digit) | `20241224_letter_DGP...` |
| Missing date | `AHFL Area Statement .pdf` | Keep descriptive name, no date prefix |

**Detection rule**: If a filename starts with 8 digits, test both DDMMYYYY and YYYYMMDD interpretations. If the month digit is 13+ or the day is 32+, it's likely in the other format. Dates like `19082014` (day=19 > 12, month=08 ≤ 12) are DDMMYYYY. Dates like `20140819` (year=2014, month=08, day=19) are YYYYMMDD.

**Standard**: Always convert to YYYYMMDD — it's sortable, unambiguous, and the ISO standard.

### 2. Spelling & Typo Fixes

| Typo | Correction | Context |
|---|---|---|
| `wiht` | `with` | Common preposition typo |
| `form` | `from` | Similar-sounding preposition error |
| `sekech` / `Sekech` | `Sketch` | Architectural/engineering context |
| `letter f` | `letter_from` | Abbreviated word |
| `Navakalyan Muth` | `Navakalyan Math` | Trust/institution name correction |
| `k srirsm` | `K_Sriram` | Person name, likely OCR or transcription error |
| `Hub` (truncated) | `Hubli` | Place name needs full expansion if source Drive data shows a longer name |
| Trailing space before `.pdf` | Remove space | e.g. `Area Statement .pdf` → `Area_Statement.pdf` |

### 3. Missing File Extensions

Some files in the Drive listing have no extension. Add `.pdf` (or the actual format) when:
- The file has a descriptive name but no `.pdf` suffix
- The Drive metadata shows `mimeType: application/pdf`

### 4. Duplicate Handling

When the same filename appears N times (different file IDs, possibly different sizes), suffix each distinct copy:

```
20140819_NOC_issued_by_fire_service_copy1.pdf
20140819_NOC_issued_by_fire_service_copy2.pdf
20140819_NOC_issued_by_fire_service_copy3.pdf
20140819_NOC_issued_by_fire_service_copy4.pdf
```

**Include the Drive file ID in the description** so duplicates remain traceable to their source.

### 4b. Size-Based Duplicate & Variant Detection

File sizes are a powerful signal when filenames suggest duplicates:

| Size Pattern | Meaning | Action |
|---|---|---|
| **Same name, same size, same date** | True duplicate (bit-for-bit identical) | Use `_copy1`, `_copy2` to imply one is a redundant copy |
| **Same name, same date, same size to KB** | Same document variant | Use `_a`, `_b` suffix — avoids implying one is the "original" and the other is a "copy" |
| **Same type, same lab, same name structure, BUT different sizes (e.g. 22-27MB vs 10.3MB)** | Different substrate or day — belongs to separate batches | Group each size-range batch independently; number sequentially within each batch |
| **Single file with unique size** | Likely a distinct document | Standardize name normally; no variant suffix |

**Practical approach**: When you can't download files (Drive auth barrier), sort by size as a proxy for content uniqueness. Files with identical sizes to the byte are almost certainly exact duplicates. Files with similar-size ranges (within 20%) that share a naming pattern likely belong to the same batch.

### 4c. Batch Grouping by Size Range

When multiple files of the same document type have no date but fall into distinct size clusters:

1. **Identify size clusters** — group files with similar sizes (e.g., 6 files at 22-27MB, 3 files at 10.3MB)
2. **Treat each cluster as a separate numbered batch** — use zero-padded sequential numbering within each batch
3. **Use different numbering scope per batch** — `undated_Project_Pour_Card_01` through `_07` for one batch, `undated_Project_Pour_Card_1` through `_3` for another (or keep them all in one sequence if content overlaps — use judgment)
4. **Document the batch logic in the description field** so a reviewer understands why, e.g., "Batch A (22-27MB scans)" vs "Batch B (10.3MB scans)"

### 4d. Gap Preservation in Numbered Series

When a numbered series has gaps (e.g., `(1)`, `(2)`, `(4)` — no `(3)`):

- **Preserve the original numbering** — do NOT renumber sequentially. The gap may mean file (3) was never uploaded, was deleted, or belongs to a different folder.
- **Note the gap in the description** — `"No file '(3)' exists in the series"` — so the user knows to look for it if needed.

### 5. Truncated or Incomplete Names

When a filename is clearly cut off mid-sentence (e.g., `the secretary council of`), infer the completion from context:

- `C council of` → `Council_of_Architecture`
- `DGP Fire Service Bangalore to the Commissioner...` → expand truncated city/name from known relationships

## Standard naming convention

```
YYYYMMDD_Project_Entity_Description[_variant].pdf
```

Rules:
- **Dated files**: Date prefix in YYYYMMDD, then snake_case
- **Undated files**: Prefix with `undated_` + descriptive name — never guess a date. This makes undated files sort together at the top/bottom of a listing and signals to the user that the date needs filling in.
- **Project reference** (optional but preferred): e.g., `AHFL_Stelo_` for project-scoped docs
- **Zero-padded numbers**: `01` not `1` for sequential batches (ensures correct sort order)
- **Duplicates**: See §4 above — use `_copy1`, `_copy2` or `_a`, `_b` depending on context
- **No trailing spaces** before extensions
- **No special characters** beyond underscores and hyphens
- **Organizational acronyms**: Uppercase consistently. `Ahfl` → `AHFL`, not mixed case.

## Construction / Civil Engineering Doc Types

When standardizing construction project folders (pour cards, test reports, checklists, invoices), use these normalized document type names:

| Raw Name | Standardized Type | Notes |
|---|---|---|
| `Concrete Pour Card`, `Pour card`, `Concrete Pour Card Ahfl` | `Concrete_Pour_Card` | Pour cards record date/time/volume/grade/weather of concrete pours |
| `Concrete cubes test report`, `Cubes Test Report`, `Test Report` | `Concrete_Cubes_Test_Report` | Compressive strength test results for concrete cubes (include testing lab name) |
| `Checklist RCC Works`, `Check List Slab`, `Checklist` | `Checklist_[Area]` | Merge `Check List` → `Checklist`. Suffix the area/structure (e.g., `RCC_Works`, `Slab`) |
| `Tax Invoice`, `Invoice` | `Tax_Invoice` | Always prefix with vendor name: `Tax_Invoice_VendorName` |
| `Housekeeping Attendance`, `Attendance` | `Housekeeping_Attendance` | Site labor attendance sheets |

**Testing Lab Name Mapping** — these appear in cube test report filenames and should NOT be expanded (they're college engineering labs; the acronym is the name):

- `SSS` — SSS Testing Lab
- `CAT` — CAT Pvt Ltd Testing Lab
- `BV_BCET` — Basaveshwar Veerashaiva College of Engineering & Technology
- `JMS` — JMS Testing Lab
- `NTLR` — NTLR Testing Lab
- `SCET` — SCET (college engineering lab)
- `SDM_CET` — SDM College of Engineering & Technology, Dharwad

Keep acronyms as-is in filenames; expand in the description field for traceability.

## Workflow: Filename-Only Audit (When Files Are Inaccessible)

When Google Drive files redirect to a sign-in page and cannot be downloaded, you can still produce a thorough analysis from what's visible:

1. **Record all filenames** from the folder listing — note sizes, dates, and any pattern in names
2. **Classify each file by type** — infer from the filename (e.g., "test report" → Test Report, "pour card" → Pour Card)
3. **Detect duplicates** by comparing sizes — same-size files on the same date are likely duplicates or variants
4. **Identify batches** by size-range clusters — group similar-size files of the same type
5. **Check for gaps** in numbered series
6. **Standardize** — apply the naming convention to every file, document every fix in the description field
7. **Mark undated** — prefix with `undated_` for any file without a date in its name
8. **Flag unknowns** — genuinely ambiguous files (e.g., `AHFL Doc.pdf`) should get a generic name with a note in the description

Output a complete JSON array (old_name → new_name) with the Drive file_id where known.

When Google Drive shared links redirect to a sign-in page:

1. First try: `curl` with `?export=download&id=FILE_ID`
2. If that yields an HTML login page, try with confirm cookie from the HTML
3. Fallback: `browser_navigate` to the preview URL
4. If all methods yield Google sign-in → **work with the filename metadata alone**. The filenames and descriptions from the folder listing are often detailed enough to perform the audit.

**Do NOT fabricate file content.** Report that the files require authentication but proceed with what the filenames tell you — dates, names, typos, and structural issues are visible in the names themselves.

## Parallel Analysis for Large Folders

For folder trees with 100+ files across multiple sub-folders, see `draas-drive-organization/references/bulk-file-naming-standardization.md` §"Scaling: Parallel Sub-Agent Analysis for 100+ Files" for the concurrent sub-agent workflow.

## JSON output format for rename manifests

When producing a rename manifest (old_name → new_name mapping), use this structure:

```json
[
  {
    "old_name": "original filename with typos.pdf",
    "new_name": "20240101_Standardized_Description.pdf",
    "folder": "Source Folder Name",
    "description": "Explanation of what was fixed and why. Include Drive file ID for traceability."
  }
]
```

The description field is critical — it documents every change (spelling fix, date correction, duplicate number) so a human reviewer can verify without cross-referencing.
