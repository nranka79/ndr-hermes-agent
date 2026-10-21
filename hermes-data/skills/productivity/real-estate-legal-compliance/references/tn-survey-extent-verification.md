# TN Survey Extent Verification — resolving 35-vs-36-cents type discrepancies (verified 2026-09-16)

Use when NDR (or a vendor sheet) gives a list of survey numbers and internal spreadsheets
disagree on the extent (e.g. 167/2C = 0.35 in one tab, 0.36 in another), and the user asks
"what does the original sale deed say?"

## Source-of-truth hierarchy (highest first)

1. **The registered sale deed's Schedule of Properties** (the "SCHEDULE OF PROPERTIES"
   section of the scanned deed, usually ~pages 55–62 of a ~148-page master deed, right
   after the covenants and before the witness/attestation pages). It lists per-survey
   extent as "Survey No.X, Dry Ext Hec.0.MM.SS (or) Ac.0.XX cents, Asst.Rs.Y np., Full Extent"
   and ends with "Item Nos.1 to N altogether making a total extent of Ac.T.TT".
2. **Current Patta / ILR (Integrated Land Record) / FMB sketch** — the revenue authority.
   The patta's Ha-Ares-Sqm notation "0-14.50" = Hect 0, Ares 14, Sqm 50 = 0.145 Ha.
3. Internal tabulations (Reg Sy No Details, Sevaganapalli Accounts, Kagganur Master Data) —
   corroborate, but they round inconsistently (0.35 vs 0.36 both appear from the same
   revenue data).

## Key conversion: Ha-Ares-Sqm → cents

- Patta/ILR/FMB show extent as `H-AA-SS` (Hectares–Ares–Sqm). `0-14.50` = 0.145 Ha.
- 1 Ha = 2.47105 acres = 247.105 cents. So **0.145 Ha = 35.83 cents ≈ 36 cents**.
- The "0.35" rows in internal sheets are a rounding-DOWN of 35.8c; the patta-based figure
  is 0.36 (Sheet2 with assessment Rs.0.72 matches the patta's Asst column exactly).
- When an internal sheet prints a Hec column like "0.14.5" (no ares/sqm split) plus acres
  like "0.36", the hectares figure is the authoritative one; the acres cell may be sloppy.

## Verification procedure (with OCR)

1. Find the deed PDFs in Drive (search name for the doc no / date / "sale deed").
   A 148-page master deed scan is ~60 MB; the certified copy is smaller (~9.7 MB, ~142
   pages) and contains the same schedule — page offsets differ by scan cropping, so grep
   the whole document.
2. Render + OCR in batches with pymupdf (`page.get_pixmap(dpi=200)`) + tesseract
   (`-l eng --psm 6`). Cheap and adequate for English deed bodies.
3. Locate the Schedule of Properties; grep every page for the survey prefix (`167`) and
   list item numbers; confirm the closing total row matches the deed's known total.
4. **Do not assume a survey is in a given deed.** Example: NDR believed 167/2C was part of
   the FIRST Sevaganapalli master deed (doc 21201/2023 dated 16-10-2023, 7.53 acres,
   ~116 vendees/signatories). OCR of all 148 pages proved the schedule has exactly 19
   items (158/1A1A … 167/2D — the 167-series there is only 167/1A, 1B, 1D, 1H, 1I, 2D)
   totalling exactly 7.53 ac. **167/2C is NOT in that deed** — it was registered via a
   separate instrument (exchange deed 3906/2024 with Suresh & Manjunath Reddy).
5. Pull the current patta/ILR/FMB for the survey (search Drive for "Patta <survey>",
   "ILR Sy No", "FMB") — the patta issued to the project entity after registration is the
   definitive extent + patta no. For 167/2C: **Patta No 2205 in the name of Sevaganapalli
   Land Partners, 0-14.50 Ha = 35.8c ≈ 36 cents**.
6. Report: the deed does/doesn't contain the survey, what the deed schedule says, what the
   patta says, and which internal-sheet figure is right.

## Follow-up session 2026-09-18 — 167/1I, deed numbering, and A/B schedules

### TWO reference numbers on the same exchange deed (caused confusion)

The 14-11-2024 exchange deed carries both:

- **Doc No. 3906/2024** — the SRO registration number. **Cite this one** (matches the
  SRO register, the EC entry, the internal tracking sheet, and the Drive filename).
- **228/2024** — the presentation / Book-I number stamped in the margin
  ("Document No. ___ of 2024 of Book-I").

Both are real, they are different fields. Do NOT "correct" the filename from 3906 to 228.

**Filename date trap:** the file is named `20250703 Copy of Exchange Deed No 3906 Sy No
167(2C)` — **20250703 is the scan/copy date, not the deed date**. The deed is dated
14-11-2024. Trust the deed text for the date, the filename for the doc number.

### Full A/B schedules of the 14-11-2024 exchange (3906/2024)

Parties: Y Suresh Reddy & family (Suresh Reddy, Deepak S, Pavan Reddy, Y Manjunath Reddy,
minors Adith Kiran Reddy + Janith M Reddy, all of Sevaganapalli) ↔ Sevaganapalli Land
Partners (Nishant Ranka, Srinivas Krishnappa, via SPA holder Rajendra S V under SPA
0557/2023, Book-4, Shivaji Nagar).

**A-SCHEDULE — SLPP receives** (value Rs 25,20,000):
- Sy 167/2C — Dry, Hec 0.14.5 (or) Ac **0.36 cents**, Asst Rs 0.72, FULL EXTENT.
  Boundaries: East Sy 158 & 167/2D; West 167/2B; North 167/2B & 158; South 166.

**B-SCHEDULE — SLPP gives away, total Ac 0.52** (value Rs 36,40,000):
1. Sy 158/1A1A — Hec 0.14.50 (Ac 0.36), Asst 0.73
2. Sy 167/1A — Hec 0.01.50 (Ac 0.04), Asst 0.07
3. Sy 167/1B — Hec 0.01.0 (Ac 0.03), Asst 0.06
4. Sy 167/1D — Hec 0.01.0 (Ac 0.03), Asst 0.06
5. Sy 167/1H — Hec 0.02.5 (Ac 0.06), Asst 0.12

**Check this every time:** 167/1A, 1B, 1D and 1H appear in BOTH the 2023 master sale deed
(acquired, 0.04/0.03/0.03/0.06) AND this exchange (given away). They were swapped out.
**Never list them as current SLPP holdings.**

### 167/1I — the mirror case

**167/1I = 0.07 ac** (Hec 0.02.5, Asst Rs 0.12). Conveyed by the master Sale Deed
16-10-2023, Doc **21201/2023** (Item 27). Confirmed twice — the deed's own Schedule of
Properties and the Induslaw title report (20250905). **There is NO exchange deed for
167/1I; it was never exchanged and remains with SLPP.** When the user asks for "the
exchange deed for 167/1I", the correct answer is that none exists — give the sale deed.

Current 167-series position: **1I (0.07, retained) + 2C (0.36, gained by exchange
3906/2024) + 2D (0.06, retained)**.

### The 7.53 ac vs 7.29 ac gap is NOT an error

The master deed 21201/2023 has 19 schedule items summing to exactly 7.53 ac. NDR's working
survey list totals 7.29 ac. His list is the SUBSET of survey numbers that went into the
DTCP sanction. Do not chase the 0.24 ac difference as though the deed were wrong.

Related arithmetic NDR cross-checks (title vs sanction area): 7.29 ac × 43,560 =
3,17,552 sq ft ÷ 10.76 = **~29,513 sq m** vs the sanction letter/layout's **30,416 sq m**
→ apparent ~903 sq m excess. Resolution path: (1) which surveys are actually in the
sanction plan vs the title schedule, (2) land given away by exchange after sanction,
(3) road relinquishment / kharab deductions, (4) whether the sanction includes adjacent
government land. NOTE: NDR sometimes says "guntas" when he means cents — TN is cents,
Karnataka is guntas.

### Fastest route to a "what is the extent of Sy X" answer

The **Induslaw title report** (`20250905 Ranka Oasis Induslaw Title Report`, owned by
ndr@draas.com) states per-survey extents AND the conveying instrument in one document —
grep it FIRST, before OCRing a 148-page deed. Fall back to deed OCR only when the report
is silent or the user explicitly asks for the deed's own wording.

### OCR method for these TN deed scans

- `pymupdf` renders via `page.get_pixmap(dpi=210)`; these deeds are pure scans with NO
  text layer (a 148-page deed returns only stray page numbers).
- **Run `tesseract` one page at a time** — batching many pages inside a single Python loop
  blows the 180s terminal timeout. Render a batch first, then loop tesseract with a
  per-page `timeout 90`.
- The schedule sits ~25–40% of the way in (page 8 of 25 for the exchange deed; near the
  Assessment/UDR tables for the big aggregation deeds). grep the OCR dump for `SCHEDULE`,
  `Survey No`, `Extent`, `Hec`, `Ac.` rather than reading page by page.
- **Which venv:** only `/opt/hermes/.venv` has `googleapiclient` (all `/opt/data/.venv*`
  lack it); `/opt/data/.venv-render` has pymupdf. Invoke as
  `sys.path.insert(0,'/opt/hermes'); from tools.gws_auth import build_service;
  build_service('drive','v3',service_name='google-draas')`.

## Pitfalls

- The first/biggest deed in the firm's name is not necessarily the only deed — later
  exchange/addendum deeds (e.g. 3906/2024, 21785/2024, 4350/2024) added individual
  surveys. Always check the survey's current patta ownership, not just the first deed.
- OCR quality: the "12" in "167/1I" (letter I) vs "1I"/"11" confusions abound; grep both
  "167/1I" and "167/11". The vendor list (pages 4–51) and GPA lists (pages ~40–51) repeat
  the full survey roster per GPA — cross-check the schedule against a GPA paragraph for a
  second read.
- Deed schedule assessment column (Asst.Rs) matches the patta's assessment — a cheap
  consistency check between deed and revenue record.
- Vault/DWD scope note: DWD drive media download works with
  `t._creds_for_target(email, scopes=['https://www.googleapis.com/auth/drive'])` + googleapiclient
  in a terminal() subprocess (see gws-domain-admin skill).