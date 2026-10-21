# EC Transaction Review → Pending Deeds & Incomplete Documents Register

Proven workflow (Besthamanahalli/Anekal EC set, Sep 2026): turn a multi-tab
EC review spreadsheet into a cleaned, flagged register of every PENDING /
INCOMPLETE document (open mortgages, outstanding agreements, orphan
cancellations, sale+later-agreement conflicts) with full registration numbers,
ready to hand to counsel for chasing.

## Source data shapes you'll meet

EC review workbooks come in two flavors — handle both:

1. **Per-survey summary tabs** — one tab per survey number, rows = documents
   in that survey's EC. Often combined into master tabs:
   - `Transaction History` (transaction-level: Sl No, Survey No, Extent,
     Date, Type, Document No., From → To, Consideration, EC Source)
   - `Survey Master` (survey-level: survey no, extent, landowners, in-old-EC?,
     in-new-EC?, #old txns, #new txns, Red Flags / Remarks)
   - `Comparison / Red Flags` (survey-level old-vs-new EC comparison)
2. **Consolidated transaction dumps** — one row per doc with a `Schedule`
   column listing every survey the document covers (e.g. one Sale covers
   `Sy 98/2, Sy 99/2, Sy 99/4`). These rows repeat per survey — dedupe.

Also read the sibling **Survey Number Document Index** spreadsheet if present
(it has a `Transaction Summary` tab with Drive links per document) — it is
the link source for the register.

## Bulk-read pattern (Sheets API rate limit — CRITICAL)

Dumping many tabs one `values().get()` at a time hits the **60 reads/min per
user** Sheets quota and dies with HTTP 429 partway through. Use batchGet —
ONE API call for the whole spreadsheet:

```python
ranges = [f"'{s['properties']['title']}'" for s in meta["sheets"]]
for i in range(0, len(ranges), 40):          # chunk to stay safe
    resp = svc.spreadsheets().values().batchGet(
        spreadsheetId=FID, ranges=ranges[i:i+40]).execute()
    for vr in resp.get("valueRanges", []):
        title = vr["range"].split("'")[1]
        vals  = vr.get("values", [])
```

Add an exponential-backoff retry on `429`/`RATE_LIMIT` (base 3s, 6 attempts).
Fetch sheet metadata once with `fields="sheets.properties(title,sheetId)"`
and reuse it.

## Document classification rules (per survey, chronologically)

Sort each survey's rows by date (`DD-MM-YYYY`), then classify every row:

| Document type | Status → Flag | Condition |
|---|---|---|
| DTD / mortgage | **OPEN MORTGAGE → RED** | no later discharge deed on same survey |
| DTD / mortgage | MORTGAGE - DISCHARGED → INFO | later discharge exists (cite its doc no) |
| Discharge deed | DISCHARGE DEED → INFO | clean; AMBER if a LATER DTD appears after it (verify chronology) |
| Agreement (possession not given) | **OPEN AGREEMENT → AMBER** | no later sale OR cancellation on same survey |
| Agreement (possession given) | AGREEMENT (possession GIVEN) → AMBER | may operate as conveyance; verify registered sale |
| Agreement | AGREEMENT - PERFORMED/CANCELLED → INFO | followed by sale or cancellation |
| Cancellation deed | **ORPHAN CANCELLATION → AMBER** | no earlier agreement/sale/GPA in the same survey's EC to cancel |
| Cancellation deed | CANCELLATION DEED → INFO | underlying doc present in EC (cite it) |
| Sale deed | **SALE + LATER AGREEMENT → AMBER** | later agreement still on record — verify cancellation |
| Sale deed | SALE DEED → INFO | clean |

**Survey-level flags** to ALSO carry over (they don't always appear as rows in
the transaction tab):
- `OPEN DTD` flagged in Survey Master but no DTD row in the transaction dump
  → reconstruct the row from the consolidated-dump data for that doc no
  (e.g. CMPD60 → 32 surveys, one RED row each, even though only ~20 appear
  in the transaction tab).
- `Old set shows N txns; new EC shows only M` → DROPPED TRANSACTIONS (AMBER)
- `NO transactions in new consolidated EC` → zero-transaction parcel (AMBER)
- `No registered sale deed in EC period` → title rests on agreement chain (AMBER)
- `Cancellation … no earlier agreement in this EC period` → orphan (AMBER)

## Register spreadsheet shape (4 tabs, openpyxl)

1. **Pending Documents Register** — every RED/AMBER doc row. Columns: Survey
   No, Date, Doc Type, Doc No (short: `CMPD60`), Registration No (full:
   `CMPD60 (CMP-1-03309-2012-13)`), Consideration, Parties (From → To),
   Status, Flag, Issue/Action Needed, EC Source, In-scope? (series flag),
   Drive Link/File. Arrangement: **group by Survey No (natural sort: 80/1 →
   82/2 → 93 → 93* → 102/2 …), and within each survey list dates NEW → OLD**
   (Prakash's standing arrangement, 2026-09-23 — latest transaction first so
   each survey reads back from the current position). Rebuild existing
   registers into this order with clear+rebuild + RAW date column, never in
   place; see `google-workspace/references/sheets-row-reorder-and-date-serial.md`
   §4–5 for the natural-sort key and write-back date corruption fix.
2. **Survey-Level Issues** — one row per survey-level flag (dropped txns,
   zero txns, no sale deed) with extent + RTC landowners columns.
3. **Open Mortgages (RED)** — summary: survey, date, doc no, reg no, lender,
   borrower, status, action. Dedupe repeated doc rows per survey.
4. **Full Transaction Ledger** — ALL rows incl. INFO/clean, for cross-ref.

Styling: RED fill `F4CCCC`, AMBER `FCE5CD`, INFO/green `D9EAD3`, scope column
highlight `FFF2CC`; header dark blue `1F3864` white bold; freeze `A2`;
auto_filter on the full range. Mind the em-dash pitfall — use ASCII in cell
values that go to Sheets (openpyxl local xlsx is fine, but the Google Sheets
upload path is not).

## Delivering to Drive

Upload the local .xlsx twice:
- As a **Google Sheet** (`mimeType: application/vnd.google-apps.spreadsheet`)
  so the user gets a clickable/editable link
- As a **native .xlsx copy** in the same folder

```python
drive.files().create(body={"name": name, "parents": [FOLDER],
    "mimeType": "application/vnd.google-apps.spreadsheet"},
    media_body=src, fields="id,name,webViewLink").execute()
```

Verify the upload by reading back the header + first rows of the Google Sheet
— conversion preserves values; confirm it did not drop tab names or color flags.

## Pitfalls

- **Duplicates in the raw history**: the SAME doc rows repeat when a deed
  covers multiple surveys OR when old/new EC both list it. Dedupe by
  (survey, date, type, doc_no, source) after classification; count and keep 1.
- **Short vs full doc numbers**: always carry BOTH (`CMPD60` and
  `CMPD60 (CMP-1-03309-2012-13)`). Counsel needs the full registration
  reference; the user quotes the short form.
- **Parties string is one blob**: split on ` → ` into grantor/grantee for
  the Open Mortgages tab; normalize known lenders by name match (e.g. any
  row containing "Tetron" → `TETRON COMMERCIAL LIMITED`).
- **Scope re-slicing**: when the user later scopes a report to a survey
  series (e.g. Sy 80–110), keep the scope+flag columns in the register so
  both the scoped and full views stay usable without rebuilding.
- **Drive-link enrichment**: attach Drive links from the Document Index's
  Transaction Summary by matching the survey column; when a survey has many
  docs, put the first link + "N docs" so cells stay readable.

## Related

- `property-title-due-diligence` (umbrella) — RTC/EC/khata reading, title
  chain, survey-wise inventories. This skill is the EC-register-specific
  extraction piece.