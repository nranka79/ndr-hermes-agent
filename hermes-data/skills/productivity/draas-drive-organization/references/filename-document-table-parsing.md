# Filename → Document Table Parsing (Sy No / Date / Doc No / Type / Parties)

When the user renames project files with dates and asks for a spreadsheet **table**:
`SL NO | Sy NO | DOCUMENT DATE | DOCUMENT NUMBER | DOCUMENT TYPE | PARTIES (from and to) | DRIVE LINK`,
sorted by date old → new, with **multiple survey numbers listed on continuation rows below** the main row.

This is the successor format to `project-checklist-categories.md` (that flat layout was the
2026-08-13 first pass; the user then renamed files and asked for parsed columns). Same delivery
rules apply: ONE spreadsheet, one tab per project, NO summary tab, tab order = user's order,
links in plain `https://drive.google.com/file/d/<ID>/view`, row colors by category/type.

## Step 0 — ALWAYS RE-WALK the folders first

User renames files in-place between requests (they said "I have updated document dates in the
file names"). Never reuse a stored inventory — counts shift (2026-08-13: Udaya 47→46,
Amber 67→66, Oasis 303→264). Re-run the walk, then re-parse from the fresh names.

## Multi-survey rendering rule

- One **Sl No per document** (not per survey).
- First row: full doc info + first Sy No. Additional surveys = continuation rows with the
  SAME Sl No, only the Sy No cell filled (date/docno/type/parties blank), link repeated.
  User wording: *"if multiple survey nos then list other Sy Nos below"*.
- Sort documents by date key old → new; undated ('') sort LAST via `r['date_key'] or '9999'`.

## Survey-number extraction (hardest part — many iterations)

Normalization targets: `158/1C9A`, `240/3`, `1508/1` (4-digit surveys exist!), `166/3E1`.

Pipeline:
1. `SURVEY_PREFIX` regex finds the clause: `\bsy(?:\.?\s*no\.?'?s?|no\.?'?s?|\.)?s?\s*[:\-]?\s*`
   — handles `Sy No`, `SyNo.`, `Sy.no -`, `Sy No's(` (possessive + paren list).
2. `SURVEY_TERM` ENDS the clause at: `.pdf`, end-of-string, ` tax|for|registered|doc|p\.no|
   applied|receipt|and others|village|b/w|between` (space-prefixed), `)`, or `. `.
   **CRITICAL: do NOT put `,` in the terminator** — comma is a survey-LIST separator
   ("Sy 166-3A 167-1D,1I" must keep the whole list). Only `)` closes a paren list.
3. Parenthesized lists ("Sy No's(174-2,175-3 and 175-4)", "Sy No 158(1C3,1C4,1C5,1C6,1C9A)")
   → capture up to matching `)`, then split.
4. Split the raw clause on `,` / `;` / ` and ` / `&` / `+`; ALSO split space-separated pairs
   like `166-3A 167-1D` (two surveys in one clause).
5. Per-token normalization (order matters):
   - strip junk: trailing `-patta|-fmb|-adangal|-udr|-applied|-copy|-receipt|-tax...`,
     `\s+of\s+[A-Z].*` ("of Narayana Reddy"), `otrs|others`, `-?p\.?no\s*\d+.*`
     ("-p.no-310,444"), `& its subdivision`.
   - `(\d{3,4})-(\d{1,2}[A-Za-z]{0,3}\d{0,3}(?:-[0-9A-Za-z]+)?)` → `166/3E1`, `240/3A`,
     `176/1B2` (allow trailing digit after letters!)
   - `(\d{3,4})(\d[A-Za-z0-9]+)` → `1581A1A`→`158/1A1A`, `1641A1A`→`164/1A1A`, `15081`→`1508/1`
   - `(\d{3,4})\s+([0-9A-Za-z]+)` → `158 1A1A`→`158/1A1A`
   - already `\d{3,4}/` → keep; already `\d{1,2}/` → keep standalone ("15/1A")
   - else inherit the LAST seen full survey's prefix (`inherit_prefix`) → `1C9B` after
     `158/1C9A` becomes `158/1C9B`.
   - track `last_sub` (subdivision, e.g. `1C3` from `158/1C3`) to expand SHORTHAND lists:
     `158/1C3,5,6` → `158/1C3`, `158/1C5`, `158/1C6` (token is pure digits ≤3 and last_sub
     matches `^(\d*)([A-Z])(\d+)$`).
   - **Page-number junk**: if the raw clause contains `p\.?no`, DROP pure-digit tokens
     (`^\d{2,4}$`) — they are patta page numbers, not surveys. Apply BEFORE prefix inheritance
     so `444` doesn't become `164/444`.

## Document-date extraction (user renamed files to carry dates)

Order:
1. **EC period files** first (name has `\bec\b|ecc-`): YYYYMMDD start (`EC 19750401 to...`),
   DDMMYYYY start (`EC from 01011975-03042023`), `dd[-.]mm[-.]yyyy` (`EC from 20-08-1993`,
   `EC 1.1.2003`), 2-digit years with century heuristic (`>=50 → 19xx`), `01JAN1975` month-name.
   Display as `"EC " + dd.mm.yyyy` (the period START).
2. Leading YYYYMMDD — strip repeated `Copy of` prefixes first:
   `re.sub(r'^(?:copy of\s*)+', '', n)` — "Copy of Copy of 19940601..." is a real pattern.
3. Leading DDMMYYYY (`16102023`, `17112004`), then DDMMYY (`230425`).
4. `YYYY/MM/DD` / `YYYY-MM-DD` (with `.` separator too — "2026.07.27_FormII...").
5. `dtd|dated|dt DD[-./]MM[-./]YYYY`, then any embedded `DD[-./]MM[-./]YYYY`.
6. Year-only fallback: **EC files take the FIRST year** (period start — `EC LE D'SOUZA FROM
   1969 TO 1972` → 1969), **all other files take the LAST year** (avoids `2011123` typo picking
   2011 when the name says `... 0f 2017`).

**Regex gotcha:** `re.findall(r'(19|20)\d{2}', n)` with a capturing group returns ONLY the
group (`'20'`, `'19'`) — use `(?:19|20)\d{2}` non-capturing or the year becomes 2 digits.

## Document-number extraction

Strip survey clauses first (else "Sy No 240-3" yields doc no `240`). Patterns in order:
1. `doc(?:ument)?|deed|registr\w*` + `(no|n0)` + number → `Doc no 2186`, `Doc. no 5268_1980`
2. bare `(?:no|n0)\.?` + number (`No 20527 0f 2024-2025`, `No 2227(2025-26)`, `no.4515`),
   separator class `[:.\-]?` (NOT `[:.]?` — "patta no - 62" has a dash)
3. `registered as Document No.NNN` → `365`, `1287`
4. bare number after a deed-type word: `sale deed 15678`, `Exchange deed 4292`, `GPA 12434`
5. `doc for|of NNN` → Translation "for 6594".
Keep suffixes: `11721-2024`, `22229_2023`, `3320/16`, `3076/2001` are registration years.

## Document-type ordering (substring traps)

- **`survey sketch` pattern must come BEFORE `sale deed`** — "survey sketch attached to sale
  deed 1.3" would otherwise classify as Sale Deed.
- `A-Register` needs `a-register|\ba register\b` (filename "a register (1).pdf").
- Add `aadhaar|aadhar|adhaar`, `velayudham` → Legal Opinion, `po_dra|purchase order`,
  `annexure`, `panchayats endors` → Panchayat Endorsement, `layout plan\b|approved layout plan`.
- Broad "Document" bucket = signal to add a keyword, not to ship.

## Parties (From → To)

1. Skip entirely for a `NO_PARTIES_TYPES` set: EC, Adangal, FMB, Patta, UDR, A-Register,
   Village Map, Topo Sketch, Mukalika, Death/Legal-Heir/Family-Tree, ITR, Bank Statement,
   CA Certificate, Tax, Financial, Request Letter, Builder Profile, GST/PAN/TAN,
   Incorporation/MOA/AOA, Ack, Layout/Plan/Building/RERA/Architect/NOC, Legal Opinion/Report/
   TSR, Change of Firm Name, Receipt, Legal Set, Translation, Endorsement, Annexure, Aadhaar,
   Purchase Order.
2. Strip: `Copy of|original|colour copy|certified copy|scan copy`, survey clauses, doc numbers,
   `dated? DD-MM-YYYY` AND any embedded `DD[-./]MM[-./]YYYY` (dtd date can pollute parties),
   `\b\d{6,8}\b`, `(...)` parentheticals, then `_` → space.
3. Extraction order:
   a. `(from|by|between|btwn|b/w|b_w|betwn) X (to|in favour of) Y`
   b. `(between|btwn|b/w|b_w|betwn) X and Y` **without "to"** → X = From, Y = To
      (sale-deed style "Btwn Prakash Reddy & others and Dra Thindlu Land Partners").
   c. generic `X to Y` (catches `_to_` FormII after underscore→space).
   d. from/by/between X alone; `for Y` alone.
4. Cleanup: strip trailing `for|sy|doc|registered|document|no` clauses, trailing `of YYYY`,
   trailing `other(s)|otrs`, and LEADING deed-type words from From ("SPA Sevaganapalli..." →
   "Sevaganapalli..."). Then join `f"{frm} → {to}"`.

## Pitfalls

- **Re-walk before parse** (user renames files between requests; counts shift).
- **Comma is a survey separator, not a clause terminator.**
- **4-digit surveys exist** (`1508/1`) — never hardcode `\d{3}`.
- **Non-capturing groups in `findall`** for year extraction.
- **EC = first year, others = last year** in the year-only fallback.
- **`valueInputOption='RAW'`** when writing filename-derived values (date-like tokens).
- **Verify by list-equality** of sheet rows vs JSON-sorted names — not by scanning display dates
  (year-only `1975` vs `01.01.1975` both key to the same date; display-scan false-fails).
- Continuation rows for extra surveys should still carry the Drive Link (clickable), but blank
  other cells; do NOT merge cells vertically (stale-merge trap from the earlier layout).
