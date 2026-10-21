---
name: ec-transaction-review
description: >
  Class-level workflow for EC-transaction due diligence on Indian land
  aggregations: extract red flags from an "EC review / EC transactions"
  spreadsheet (survey-review + transaction-log + old-vs-new EC comparison
  tabs), identify missing/missed transaction flow, build a verification
  report (.docx) scoped to the deal's survey range, and overlay seller-entity
  intelligence (MCA, live court cases, ED/PMLA, RERA restraints). Use when
  the user says "extract all red flags from the EC spreadsheet", "flow of
  transactions missed or missing", "generate a verification report", or asks
  to add litigation/complaints of the seller company/directors to the report.
metadata:
  hermes:
    tags: [real-estate, due-diligence, ec, encumbrance, title, red-flags, verification, pmla, rera, karnataka]
    category: domain
    related_skills: [karnataka-land-title-due-diligence, property-title-due-diligence, litigation-case-research, business-dossier, real-estate-legal-compliance]
---

# EC Transaction Review — Red Flags & Verification Report

Class-level workflow for turning an EC-transaction spreadsheet into a
verification report for a land aggregation purchase. Built from the
Besthamanahalli / Sanchaya lands session (2026-09-22) and applicable to any
DRA land aggregation with 50+ survey parcels and a 70+ EC set.

This skill owns the spreadsheet-driven red-flag taxonomy and Pending-Deeds
Register workflow. When the input is raw EC/registered-instrument PDFs
instead of an EC-transaction spreadsheet, and encumbrance review is one
workstream inside a full ground-up investigation, use
`karnataka-land-title-due-diligence` Stage 8 instead.

## When to Use

- User shares an "EC review" / "EC transactions" spreadsheet covering a land
  aggregation and asks for red flags.
- User asks to identify "flow of transaction missed or missing" from EC data.
- User asks for a "report for the verifications" (red flags + entity issues).
- User asks to add litigation / complaints / company issues of the seller
  entity or its directors/management to the report.
- User scopes the work to a survey-number range ("80 series to 110 series").
- User asks to "extract all the pending deeds" / "documents not cancelled or
  incomplete" / "flag all incomplete transactions, agreements, mortgages" /
  "to a new spreadsheet with document nos". → produce the **Pending-Deeds
  Register** (section 7) instead of/in addition to the .docx report.

## Workflow

### 1. Locate & dump the spreadsheet
- The spreadsheet usually lives next to the EC PDFs in a Drive folder like
  `bestamanahalli Lands - EC as on 7.8.26`. Search Drive by name variants
  (Bestamanahalli / Besthamanahalli / Bestamanahal).
- Dump ALL tabs to JSON with Sheets API (`values().get`, FORMATTED_VALUE).
  Do NOT hand-read 199 rows — extract programmatically.

### 2. Understand the three-tab anatomy (expect these)
1. **Survey review tab (often named Sheet1)**: one row per survey; a single
   cell packs a full transaction list — `DD.MM.YYYY: Type — ₹amount | Doc
   <REG-1-…> | Parties: …` — plus a Remarks column that already carries ⚠
   flags written by whoever reviewed the 71 ECs.
2. **Transaction log tab**: flat rows (Sl No, Survey No, Date, Type, Document
   No, From, To, Consideration, Market Value, Property/Schedule, Notes). A
   multi-schedule agreement (e.g. ANKD1441) spans MANY rows — one row per
   schedule item, only the first carries consideration.
3. **Comparison & Red Flags tab**: per-survey cross-check of the OLD EC set
   (e.g. 71 individual ECs) vs the NEW consolidated EC. Comes with flags like:
   - `Old set shows N txns; new EC shows only M — possible missing transactions`
   - `OPEN DTD <date> <doc> — no discharge deed on record`
   - `Survey present in new consolidated EC only (not among the 71 ECs)`
   - `Survey in 71-EC set but NO transactions in new consolidated EC`
   - `still open (no cancellation/sale after)`
   - `no earlier agreement in this EC period (verify what it cancels)`

### 3. Extraction method
1. Run counters + per-survey issue registers in Python: flag-category counts,
   missing-transaction delta (old−new), open-DTD list, open-agreement list,
   cancellation-without-underlying list, coverage-gap lists.
2. Normalize survey names: strip trailing `*` (converted N.A. land marker),
   merge duplicates (93 vs 93*). Filter by base survey number when scoping.
3. Build report tables: summary counts, top-N missing-transaction table,
   per-parcel register (survey → issues → action required).

### 4. Red-flag taxonomy (patterns repeat across aggregations)
| Flag | Meaning | Priority |
|---|---|---|
| OPEN DTD CMPD60 (30-08-2012 → Tetron) | mortgage, no discharge on record | CRITICAL — live third-party interest |
| Missing transactions (old>new) | new EC drops history | CRITICAL — unbroken chain unproven |
| Zero txns in new EC | EC incomplete or land excluded | CRITICAL |
| Open agreement (no cancel/sale after) | counterparty right still live | HIGH |
| Cancellation w/o underlying doc | can't tell what was cancelled | HIGH |
| Only in new consolidated EC | no individual EC exists | MED |
| No registered sale deed in period | title rests on agreement chain | HIGH — verify possession/GPA/mutation |
| Registered court decree (certified copy) | litigation history on record | HIGH — get the case |
| Duplicate rows / duplicate EC files | data quality | LOW |

### 5. Entity-overlay research (company behind the seller)
- **Company identity**: QuickCompany first (curl + grep; save page to file
  first — do NOT pipe curl into python3 for HTML parsing). Pull CIN,
  incorporation date, ROC, status, paid-up capital, directors/DINs. Tofler /
  CompanyCheck for financials + charges statement. "Company has NO registered
  charges" vs EC-level DTDs is a classic mismatch — flag it; recommend an MCA
  charge report.
- **"<Name> Holdings" trap**: the user may name a holding-company variant
  that doesn't exist in MCA records ("Sanchaya Holdings Pvt Ltd" vs the
  operative "Sanchaya Land & Estate Pvt Ltd"). Confirm exact name/CIN before
  relying; state the mismatch explicitly in the report. A different-city
  identical-ish name (Mumbai "Sanchay Holdings") is likely unrelated.
- **Live litigation**: Karnataka Judiciary case status — the
  `judiciary.karnataka.gov.in/karjud/cino_det.php?url_data=<token>` pages
  (surfaced via web search) render full case detail: CNR, parties, acts,
  hearing history. **curl/web-extract times out on these; browser_navigate
  fetches them fine.** eCourts national portal covers district courts but
  needs captcha (hand to user per litigation-case-research).
- **ED / PMLA**: press-release trail via web_search (`"<entity>" ED PMLA` +
  news mirrors like ANI/nasheman). Search phase = locations, persons named,
  bank accounts frozen, documents seized worth ₹X Cr. A PAO (provisional
  attachment order) is usually NOT public — absence of a published PAO does
  NOT equal clean title. Recommend RTI to ED + vendor disclosure/indemnity +
  escrow.
- **RERA**: K-RERA account-freeze/restraint orders ARE public and bite
  immediately — check parcel-by-parcel whether the MOU parcels fall inside any
  RERA-registered project of the entity (same-hobli projects are the trap).

### 6. Deliverable (.docx report)
- python-docx in `/opt/data/.venv` — the execute_code sandbox lacks python-docx;
  write the build script to a file and run with the venv python.
- Structure: scoped summary → category counts table → dedicated flag lists →
  per-parcel issue register → verification checklist → entity/litigation
  section → method/sources/limitations. Footer: "Internal verification — not
  a legal opinion".
- When the user scopes to a survey range, REGENERATE the report filtered to
  that range and put the range in the title (e.g. "Sy 80-110 Series").
- Upload to the EC folder on the user's own Drive identity (resolve vault
  service_name per session — Prakash = google-draas, slug psingh), set
  anyone-with-link reader, return the link.

### 7. Pending-Deeds Register Spreadsheet (the "extract all pending deeds with document numbers" deliverable)

When the user asks for a **spreadsheet of pending/incomplete documents**
("extract all pending deeds… numbers not cancelled or incomplete… flag all
incomplete transaction deeds, agreements, mortgage etc… to a new spreadsheet
with document nos"), build a colored xlsx register instead of a narrative
report. The .docx report proves the chain; the register gives the counsel /
vendor an executable doc-by-doc action list with registration numbers.

**Pipeline (all in code — never hand-read the 294-row log):**

1. **Sources to merge**: the CLEAR/transaction-history tab (flat rows with Doc
   No), the survey-master tab (survey-level flags), the per-transaction tab
   (Sanchya EC Transactions — carries CMPD60/ABLD128 rows with lender/borrower
   parties), and the Document-Index tab (Drive links per doc for reference).
2. **Classify every transaction row** per survey (chronological):
   - DTD/mortgage → any LATER discharge on same survey? → DISCHARGED (INFO)
     else **OPEN MORTGAGE (RED)**.
   - Discharge → any DTD *after* it? → AMBER "check chronology" (rare).
   - Agreement (AoS/ATS) → later sale OR cancellation? → PERFORMED (INFO)
     else **OPEN AGREEMENT (AMBER)**. "Possession given" variant → AMBER
     (may operate as conveyance without registered sale).
   - Cancellation → any EARLIER agreement/sale/GPA in same survey? →
     matched (INFO) else **ORPHAN CANCELLATION (AMBER)** — cannot tell what
     it cancels.
   - Sale → any LATER agreement still on record? → AMBER "verify
     cancellation" else INFO.
3. **Dedupe**: key = (survey, date, type, doc_no, source); the log carries
   duplicate rows for the same doc (e.g. CMPD60 ×3 on 82/2, ANKD1060 ×2 on
   91/1). Collapse, note dup count.
4. **Cross-source gap-fill — the critical step**: the transaction log often
   MISSES DTD rows for surveys the master tab flags as "OPEN DTD". Pull the
   missing rows from the per-transaction tab (keyed by survey + doc prefix,
   e.g. CMPD60) and append them as RED rows. Without this, the register
   under-counts open mortgages (20 vs 32 in the Besthamanahalli pass).
5. **Survey-level issue rows**: separately emit master-tab flags that aren't
   doc-level — ZERO transactions in new EC, DROPPED 8→3, NO REGISTERED SALE
   DEED — one row per survey, so scope-level gaps don't vanish.
6. **Sheet layout** (4 tabs, filters + freeze panes on all):
   - `Pending Documents Register` — every RED/AMBER doc: Survey No, Date,
     Doc Type, Doc No (short), Registration No (full, e.g. `CMPD60
     (CMP-1-03309-2012-13)`), Consideration, Parties, Status, Flag, Issue /
     Action, EC Source, In-80-110, Drive link. Sort scope-first, RED first.
   - `Survey-Level Issues (80-110)` — per-survey flags.
   - `Open Mortgages (RED)` — lender/borrower split out (Tetron Commercial
     Ltd is the classic repeat lender on wide aggregation DTDs).
   - `Full Transaction Ledger` — ALL rows incl. INFO/clean for reference.
   Colors: RED fill = live encumbrance, AMBER = pending/incomplete, GREEN =
   completed. Row count sanity: ~120 pending docs + ~30 survey issues for a
   50-parcel range is the expected magnitude.
7. **Upload + verify**: upload as BOTH a Google Sheet (mimeType
   application/vnd.google-apps.spreadsheet — keeps colors/filters) and a
   native .xlsx copy; then re-read the converted Sheet's tab list + header
   rows to confirm the conversion kept data (Docs-conversion normally
   preserves values; verify anyway).

No external model is involved: the register build is pure tabular
manipulation of the dumped CSVs/JSON.

## Pitfalls

- **Existing-title-DD skill may be read-only**: `property-title-due-diligence`
  was intended as the home for this workflow but was fs-protected when patched;
  this skill carries it instead. If property-title-due-diligence ever becomes
  writable, consolidate this content into it (section "EC Transaction Review
  Spreadsheet") and delete this skill with absorbed_into.
- **Do NOT hand-read long transaction logs.** Always dump to JSON and
  counter/extract in code; the comparison tab already carries most signals.
- **Sheets rate limit on multi-tab dumps**: per-tab `values().get` in a loop
  over 70+ tabs trips the 60-reads/min-per-user quota mid-dump (~tab 40), and
  the tail silently fails with 429 `RATE_LIMIT_EXCEEDED` / ReadRequestsPerMinute-
  PerUser. Fix: dump ALL tabs of a spreadsheet with ONE `batchGet` call (chunk
  ranges ~40 per request, retry loop with exponential backoff 3s→6s→12s… on
  429). Re-run after a fix rather than re-reading failed tabs one at a time.
- **Survey-number normalization matters**: strip `*` markers and merge
  duplicate spellings before counting, or counts double up.
- **Zero-consideration vs open items**: a ₹0 consideration on agreements/
  cancellations is normal for possession-not-given agreements; it is NOT a
  red flag by itself — only open/unclosed flows are.
- **New-vs-Old EC delta is the heart of the report**: the new consolidated EC
  can silently drop whole transactions; without them, chain of title is
  unproven. Always generate the old>new delta table.

## References

- **Serving a registered instrument by its document number** — when a lender / DD firm /
  counterparty asks for "the **MRTG Deed of document number 7049/25**" (an EC line turned
  into a document request), the recipe lives in `draas-drive-organization` →
  `references/registered-deed-lookup-and-verification.md`: registry-shorthand expansion
  (**MRTG/SD/GPA/JDA/DTD never appear in filenames** — a literal `MRTG` search returns 0),
  doc-number-token Drive search, verifying an IGR scanned deed (`pdftotext` empty →
  `pdftoppm` + `tesseract`; the page-1 stamp header OCRs unreliably, the last pages are
  annexures), the `anyoneWithLink` share-surface check, and the covering-mail shape.
- `references/ec-transaction-review-red-flags.md` — full worked example
  (Besthamanahalli / Sanchaya): spreadsheet anatomy, extraction scripts,
  flag taxonomy, entity-overlay findings (Misc/36/2020 CNR, ED PMLA details,
  K-RERA The Greens), verification checklist items, and the report scoping
  pattern.
- `references/ec-pending-deeds-register.md` — worked example of the
  Pending-Deeds Register build (22-Sep-2026): classification code sketch,
  cross-source gap-fill for CMPD60, 4-tab layout, upload+verify, and the
  output link for reference.
- `references/ec-transaction-register.md` — absorbed `ec-transaction-register`
  (2026-09): the standalone step-by-step for the **Pending Deeds & Incomplete
  Documents Register** — Sheets `batchGet` rate-limit fix (NOT per-tab `get`),
  per-document classification table, the 4-tab openpyxl register shape (Pending
  Register / Survey Issues / Open Mortgages / Full Ledger), Drive delivery as
  Google Sheet + native `.xlsx` with readback verification, and the dedup /
  short-vs-full doc-no / parties-split / scope-re-slicing pitfalls
  (`references/ec-transaction-register-extraction.md`).