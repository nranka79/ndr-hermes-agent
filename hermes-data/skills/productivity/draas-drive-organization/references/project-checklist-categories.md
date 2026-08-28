# Per-Project Documents Checklist (categorized, date-wise land section)

When the user shares project Drive folders and asks for a "Documents Checklist" with
separate category headers (Financial / Land / Firm / Approval / etc.), per project.

## User preference (Prakash, 2026-08-13) — HARD FORMAT RULE

- **ALL projects go in ONE single spreadsheet: one sheet (tab) per project.**
- **NO summary / overview tab.** Do not add one unless explicitly asked.
- Tab order = the order the user listed the projects in their message.
- **FLAT, DATE-SORTED LAYOUT (corrected 2026-08-13 — do NOT build section-header bands).**
  First-pass used gold `▶ CATEGORY` section-header rows with grouped files; the user
  rejected that: *"LET ALL THE DOCUMENTS BE LISTED BASED ON THE DOCUMENTS DATE -
  FROM OLD TO NEWEST, JUST ADD CATEGORY IN A NEW COLUMN OR DIFFERENT COLOUR FOR
  EACH CATEGORY"*. The accepted layout:
  - Row 1: title (merged A:F, navy, white bold).
  - Row 2: column headers (cream, bold) — `Sl No | File Name | Document Date |
    Category | Source Folder | Drive Link`.
  - Rows 3+: EVERY file in ONE continuous list, sorted by document date old → new
    (undated at the bottom, date shown as "—"), with a **Category column** AND
    **per-row background color by category**.
  - Frozen first 2 rows; drive links as plain `https://drive.google.com/file/d/<ID>/view`.
- **Category → row color palette** (light pastels, dark text): Financial = green,
  Banking/SBI = teal, Land = blue, EC = purple, Survey & Revenue = yellow,
  Firm = orange, Approval = pink, Legal Opinions = gray, JDA = cyan,
  Legal Heir = tan, Misc = white.
- Row colors applied via `repeatCell` with `fields: 'userEnteredFormat.backgroundColor'`
  (one request per data row — chunk batchUpdate ≤400 requests/call).
- **LAND-related documents are sorted date-wise old → new** — but in the flat layout
  this is just the global date sort; no separate Land section ordering needed.

## Folder discovery — the given link may be a PARENT

The shared link can be a parent folder containing several project subfolders
(worked example: `1I4Xg61gV8khNHCPfOmiNReqmRjt4EJEg` = "Master data for all Projects
Pre Approval", containing "Ranka Udaya - Hosur", "Ranka Amber - Whitefield",
"Ranka North Star - Yelahanka"). When the user lists N projects but provides fewer
folder links, run `files().list` search `name contains '<project>' and mimeType='application/vnd.google-apps.folder'`
to find the real per-project folders. Disambiguate by ID, not name (duplicate names exist).

## Classification rules — ORDER MATTERS (learned the hard way)

Check in this order per file (after path-based overrides):
1. Path overrides first (folders named "Approval documents", "Legal Opinions",
   "JDA documents", "Tax payments", "* firm related *", "SBI Pre-approval", etc.
   are authoritative category labels — trust the folder before the filename).
2. HEIR keywords (death certificate / legal heir / family tree) → dedicated
   "LEGAL HEIR & FAMILY TREE RECORDS" section for land-heavy projects, else fold into LAND.
3. LEGAL keywords (legal opinion / legal report / title report / TSR / legal set).
4. FINANCIAL keywords BEFORE approval — "RBI letter of approval" is FINANCIAL,
   not approval. FIN kw: ITR, bank statement, CA certificate, receipt, FCNR/RBI,
   property tax, assessment, tax payments, purchase order, demand draft, IPL form.
5. APPROVAL keywords (RERA, building licence, plan sanction, NOC, DTCP, layout approval,
   electricity board, road related, no ad no temple).
6. FIRM keywords — MUST use word-boundary regexes: `\bfirm\b` (plain substring
   'firm' matches inside "con**firm**ation"!), `\bpan\b`, `\btan\b`, `\bgst\b`,
   `\bpartnership\b`, `\breconstitution\b`, `\bndr\b`, `\bkishan\b`, `\bholding\b`.
7. EC detection: `re.search(r'(?<![a-z])ec(?![a-z])', nlow)` — 'ec' as a word
   (matches "EC 158.pdf", "EC SyNo...", "EC from ...") but NOT inside "receipt",
   "certificate", "exchange", "deed". Plus explicit 'ec from' / 'ec reflecting' / 'ecc-'.
8. LAND keywords BEFORE survey/revenue keywords — otherwise any deed with
   "Sy No 240-3" in the name falls into Survey & Revenue. LAND kw: sale deed, gift deed,
   gift settlement, partition, release, exchange, rectification, relinquishment,
   cancellation deed/agreement, agreement of sale/for sale, sale agreement, GPA, SPA, POA,
   mortgage deed, consent deed, settlement deed, registered as document, doc no,
   b/w / btwn / between, in favour, translation, land registered, JDA, development
   agreement, addendum, annexure, agreement (generic catches "Agreement for Sy.no. 166_3D").
9. REV (survey & revenue): patta, FMB, adangal, UDR, A-Register, village map, topo, sketch,
   mukalika, couvaretti, p.no, ekhata, form 10, panchayat endorsement.
10. MISCELLANEOUS.

Special-case rules:
- Oasis-style tax-paid bundles: name contains 'tax paid receipt' AND (fmb|patta|adangal|udr|p.no)
  → SURVEY & REVENUE (land-record bundles), NOT financial.
- Per-survey copies with no type word: `^copy of\s+(158|164|166|167|168)(?:[\s(]|\d)` → SURVEY
  (catches "Copy of 158 1A1A.pdf", "Copy of 1641A1A.pdf", "Copy of 166(2A).pdf").
- Bare doc-number files "Copy of 22118.pdf" → LAND (registered-deed copies).

## Document date extraction from filenames (for date-wise sort)

Try in this order; fall back to year-only, then blank ("—"):
1. Leading YYYYMMDD: `^(?:Copy of\s*)?(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?:[\s,_-]|$)`
2. YYYY-MM-DD or YYYY/MM/DD anywhere
3. `dtd|dated|dt` DD[-./]MM[-./]YYYY
4. Standalone DD[-./]MM[-./]YYYY
5. Any 8-digit DDMMYYYY (validate dd 01-31, mm 01-12, year 19xx-21xx) — catches
   "16102023", "01011975"
6. Year only `(19|20)\d{2}` → display "YYYY", sort key year-01-01.
Sort key = ISO date or '9999' (undated go last). ECs/pattas show period start year — acceptable.

## Pitfalls

- **Some Drive folders are named like PDFs** (e.g. folder literally named
  "20240927 Ack of Registration of Firm (DRA Thindlu).pdf"). Never infer a child's
  type from its name extension; check `mimeType` and group files by the accumulated
  path string, not by a tree display.
- **Tree-print bug:** `tree = {"name": children[0]['name'] ...}` mislabels the root
  with its first child's name. Fetch folder name via `files().get`, or print
  file-path groups instead of a tree.
- **Sheets API `updateBorders`:** border styles take `'color': {...}` DIRECTLY
  (`{'style': 'SOLID', 'color': NAVY, 'width': 1}`). `'colorSpec': {'color': ...}`
  → HttpError 400 "Unknown name colorSpec". (Sibling pitfall: `foregroundColor`
  must nest inside `textFormat`.)
- **Keyword matching on filenames is substring-based by default** — 'firm' inside
  'confirmation', 'pan' inside 'spandana'. Use `\b` word boundaries for short words.
- **Classifier sanity check: total classified count MUST equal the walked file count
  per project; a nonzero MISCELLANEOUS bucket is a signal to add keywords, not to ship.**

- **STALE MERGES SILENTLY SWALLOW VALUES when rewriting an already-formatted sheet
  (2026-08-13, cost ~3 debugging cycles).** After a first pass built section-header
  bands with `mergeCells`, rewriting that SAME spreadsheet with `values().clear()` +
  `values().update()` does NOT remove the merges. Any cell lying inside a previously
  merged range silently keeps its old merged layout: only the top-left (master) cell
  and cells OUTSIDE the merge receive the new value — interior cells read back EMPTY
  even though you wrote them. Symptom: random rows (exactly the rows that used to be
  merged section headers) show `['1', '', '', '', '', <link>]` — Sl No and Drive Link
  present, File Name/Date/Category/Source empty. The link column (F) sits outside the
  A:E merge, which is why it survives while B–E vanish. **Fix: do NOT try to rescue
  the old spreadsheet — recreate it fresh** (`drive.files().create` + addSheet +
  write values + format in one script). Unmerging is fragile (fetching merges needs
  `fields='sheets(data(merges))'` with includeGridData semantics that 400, and
  unmergeCells re-requesting every range is fiddly). If you MUST reuse the file, the
  reliable order is: unmerge FIRST, then rewrite — but fresh-create is simpler and
  the user cares about the link, not the file identity. Also prefer
  `valueInputOption='RAW'` for filename values so date-like tokens
  ("EC 01JAN1975 to 20MAY2026...") are never coerced to dates by USER_ENTERED.

- **Verify date order against the underlying sort_key, not the display string.**
  A checker that converts the DISPLAYED date back to an int will false-FAIL on
  year-only entries: '1975' → 19750000 vs '01.01.1975' → 19750101 look like a
  descending pair, but both sort to the same key (year-only = Jan 1). One
  "VIOLATION" of exactly this shape = no real problem. The authoritative check is:
  compare the sheet's row order to the sorted file list built from the JSON
  (`sort_key`, then name) — a list-equality test on names, not a numeric scan of
  display dates.
