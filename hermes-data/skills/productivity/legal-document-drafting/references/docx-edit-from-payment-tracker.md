# Filling a partnership/reconstitution deed schedule from a payment tracker (Drive .docx)

Proven recipe (Aug 2026, Redsol Farmers Collective reconstitution deed).

## 1. Reading a .docx from Google Drive when the "normal" paths fail

Google Docs API **rejects Office files**:
`HttpError 400 ... "This operation is not supported for this document. The document must not be an Office file."`

Drive `files().export(text/plain)` **rejects non-Editors files**:
`"Export only supports Docs Editors files."`

Correct path — download the raw binary and parse locally:
1. `drive.files().get(fileId=..., fields="name,mimeType,size")` → confirm mimeType `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
2. `drive.files().get_media(fileId=...)` via `MediaIoBaseDownload` → save bytes
3. Quick text-only extraction without any lib: `zipfile` + regex on `word/document.xml` (`<w:p>` split, `<w:t>` join)
4. For structured edits use python-docx (below)

## 2. Tooling

python-docx is often NOT in the active env. Install into a venv:
```bash
python3 -m venv /opt/data/.venv-docx
/opt/data/.venv-docx/bin/pip install python-docx
```
In execute_code: `sys.path.insert(0, "/opt/data/.venv-docx/lib/python3.13/site-packages")` (match the venv's py version).

## 3. Editing patterns that preserve formatting

### set_cell_text — replace cell content keeping font
Remove all paragraphs except the first, capture the first run's `<w:rPr>` XML, remove runs, `add_run(text)`, re-insert the copied rPr. Same idea works at raw XML level for table rows.

### Insert table rows before a marker row (e.g. a total row)
- `tr = copy.deepcopy(template_row._tr)` then fill each `<w:tc>` manually (find `<w:p>`, strip runs, append new `<w:r><w:t>`).
- **Insert in FORWARD order with `marker.addprevious(tr)`** → ascending numbering. Iterating `reversed(payers)` gives DESCENDING rows — a real bug hit this session.

### Insert paragraphs after an anchor (e.g. appending extra signature entries)
- For each multi-element block, **anchor every `addnext` on the SAME base** and add elements in REVERSE so final order is correct:
  ```python
  base.addnext(el_lbl); base.addnext(el_name); base.addnext(el_line)
  base = el_line  # advance only after the whole block
  ```
- Naive chaining `cur.addnext(x); cur = x` scrambles block order (observed: signature entries landed as 27,26,25).

### Ambiguous headings
`"INCOMING PARTNERS:"` appears BOTH in the party block (body intro) and the signature block. Locate the signature one by position (e.g. `i > 150`) or by preceding neighbor (e.g. after "Existing Partner (Fifth Partner)"). Never take the first match.

## 4. Indian rupee formatting

Do NOT re-group `f"{n:,}"` — it already contains commas and the regroup produces `₹50,0,,000`. Write grouping from the raw digit string: last 3 digits, then groups of 2:
```python
d = str(n)
if len(d) > 3:
    last3 = d[-3:]; rest = d[:-3]; groups = []
    while rest: groups.insert(0, rest[-2:]); rest = rest[:-2]
    d = ",".join(groups) + "," + last3
return "₹" + d
```

## 5. Workflow for tracker → deed filling

1. Extract tracker (read via Sheets API), aggregate per payer: name, plot no, total paid, Aadhaar, PAN.
2. Compute per-plot combined capital for co-owners (multiple payers can fund ONE plot).
3. Present the mapping + structural mismatches to the user; get ONE decision on row structure (per-payer vs per-plot; merge duplicates or not) before executing.
4. Build an updated COPY of the deed (filename with date suffix), leave the ORIGINAL Drive file untouched, upload as a new file.
5. Update ALL coherent surfaces together: the schedule table, the party block, the signature block, and clause references (e.g. "Partners 6 through 24" → "6 through 27"). Editing only the table breaks the deed.
6. Flag unresolved items BOTH in a note paragraph inside the doc AND in the chat reply (plots re-assigned from existing partners, payers without a plot, likely-duplicate names, blank share % / areas).

## 6. Pitfalls observed

- Leftover-placeholder scan must check tables AND paragraphs ("Incoming Partner P1", "[NAME OF INCOMING", "Name of Incoming").
- Multi-payer plots: both partners share one Farm Parcel number — decide one row per plot with combined names/capital, or one row per payer, per user's choice.
- Docs API failure on Office files is NOT a permissions problem — do not chase sharing; switch to get_media immediately.