# Pending-Deeds Register — worked example (Besthamanahalli, 22-Sep-2026)

Session: Prakash asked "extract all the pending deeds — numbers which are
not cancelled or incomplete — flag all the incomplete transaction deeds,
agreements, mortgage etc… to a new spreadsheet with document nos", after the
Sy 80-110 EC verification report was delivered.

Deliverable: 4-tab colored xlsx register (121 pending doc rows RED/AMBER +
30 survey-level issues + 33 open-mortgage rows), uploaded as Google Sheet +
native xlsx to the EC Drive folder, verified by re-reading tabs.

- Google Sheet: `1xWlteJoEGs7wTiyE6vj9FXVH9fwteEhSy5hHoK8vB8Q`
  `Besthamanahalli Pending Deeds & Incomplete Documents Register 22Sep2026`
- xlsx copy: `1tmBgCjCjih3i1p6N5YxwOrWUJsDfuqhY`

## Source spreadsheets (Drive folder `bestamanahalli Lands - EC as on 7.8.26`)

- `EC Review - Besthamanahalli (Anekal) - 71 ECs - 07Aug2026`
  (id `1GJZNYzS7mwz4k3_OfJC3ZhBdW29TlZpdxAdp7D3lRSc`) — tabs: Sheet1 (survey
  review with packed transaction cell + Remarks), "Sanchya EC Transactions"
  (flat log incl. CMPD60 rows with borrower/lender parties), "Comparison /
  Red Flags".
- `EC Review - Besthamanahalli (Anekal) - CLEAR v2 - 07Aug2026`
  (id `1Qpi9objeL7MnMsrnQOzXhhstyb-giXrHtWqx9lCvMT4`) — tabs: Survey Master
  (per-survey flags incl. OPEN DTD / dropped-txns / orphan cancellation),
  Transaction History (flat), Comparison.
- `Bestamanahalli - Survey Number Document Index`
  (id `1CYCeHdk2VfeVfSJzI6o56rQj6bbq5yuHYzR8rg-y6ug`) — per-sy tabs + "Sale
  Deeds ATS GPA 2012+" + "Transaction Summary" (Drive links per doc, useful
  to attach to register rows).

## Classification logic (per survey, chronological)

| Row type | Rule | Result |
|---|---|---|
| DTD / mortgage | later discharge on same survey? | DISCHARGED (INFO) else OPEN MORTGAGE (RED) |
| Discharge deed | DTD *after* it? | AMBER check-chronology (rare) else INFO |
| Agreement (AoS/ATS) | later sale OR cancellation? | PERFORMED/CANCELLED (INFO) else OPEN AGREEMENT (AMBER) |
| Agreement "possession given" | — | AMBER (may operate as conveyance) |
| Cancellation | earlier agreement/sale/GPA? | matched (INFO) else ORPHAN CANCELLATION (AMBER) |
| Sale deed | later agreement still on record? | AMBER verify-cancellation else INFO |

## Critical gap-fill (the lesson)

CLEAR v2 Transaction History had RED rows for only 20 surveys, but the
Survey Master flagged 32 as "OPEN DTD CMPD60". The log tab itself was
missing DTD rows for 12 surveys (101/5, 101/7, 101/8, 106/2, 108/1, 108/2,
108/3, 136/1B, 146/2, 146/3, 154/2, 84/1, 99/1). Fix: pull CMPD60 rows from
the "Sanchya EC Transactions" tab keyed by survey+doc prefix and append as
RED rows. Result: 33 open mortgages total (32 CMPD60 Tetron + 1 ABLD128 on
142/5).

Always cross-check master-tab "OPEN DTD" count against transaction-log DTD
rows — if master > log, the log is incomplete, not the flags.

## Dedup

Key = (survey, date, type, doc_no, source). Log carries duplicate rows for
the same doc: CMPD60 ×3 on 82/2, ANKD1060/ANK1263 ×2 on 91/1, ANKD235
partition+rectification clusters. Collapse; note dup count in remarks.

## Sheet layout (4 tabs)

1. `Pending Documents Register` — 121 rows: Survey No, Date, Doc Type,
   Doc No (short), Registration No (full), Consideration, Parties, Status,
   Flag, Issue/Action, EC Source, In-80-110?, Drive link. Sort scope-first
   then RED-first. RED fill = live encumbrance, AMBER = pending/incomplete.
2. `Survey-Level Issues (80-110)` — 30 rows: ZERO txns in new EC, DROPPED
   N→M, NO REGISTERED SALE DEED, per survey.
3. `Open Mortgages (RED)` — 33 rows, lender/borrower split (regex on
   "→" in parties; Tetron Commercial Ltd normalised).
4. `Full Transaction Ledger` — all 288 deduped rows incl. INFO, for audit.

All tabs: header fill 1F3864 white bold, freeze A2, auto_filter on, column
widths per content, thin borders, wrap text.

## Code sketch

```python
# classify_document(sy, rows) — rows sorted by parse_date(dd-mm-yyyy)
# later_rows = [r for r in rows if date(r) > date(this)]
# DTD rule : discharges = {norm_doc(r.doc) for r in later_rows if "discharge" in r.type.lower()}
# agreement : has_sale = any("sale" in t and "agreement" not in t and "discharge" not in t ...)
# norm_doc: re.match(r"([A-Z]+-?\d+)", doc) -> CMPD60, ABLD118, ANKD1441
```

## Upload + verify

Drive `files().create` with `mimeType: application/vnd.google-apps.spreadsheet`
converts xlsx → Sheets (colors/filters survive); ALSO upload native xlsx copy
(named "… (xlsx copy).xlsx"). Then `spreadsheets().get` tab list + read
header rows of converted Sheet to confirm data survived conversion.

## Output numbers (sanity baseline for a ~50-parcel range)

- ~121 pending doc rows (33 RED + 88 AMBER), ~30 survey issues,
  ~288 full ledger rows.
- 32 CMPD60 open mortgages — one registration number
  (CMP-1-03309-2012-13) spanning the whole aggregation; repeat-lender
  pattern is common (Tetron Commercial Ltd).