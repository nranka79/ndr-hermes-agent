---
name: ec-transaction-register
description: >
  Turn a multi-tab EC (encumbrance certificate) review workbook into a
  flagged Pending Deeds & Incomplete Documents Register — open mortgages,
  outstanding agreements, orphan cancellations, dropped transactions —
  with full registration numbers, ready for counsel. Covers the Sheets
  batchGet rate-limit fix, per-document classification rules, the 4-tab
  openpyxl register shape, and Drive delivery as Google Sheet + xlsx.
metadata:
  hermes:
    tags: [ec, title, due-diligence, karnataka, land, sheets, register]
    category: domain
---

# EC Transaction Register Extraction

See `ec-transaction-register-extraction.md` for the full workflow.

## When to Use

- User has an EC review spreadsheet (multi-tab per survey) and asks to
  extract "all pending deeds / numbers not cancelled / incomplete
  transactions, agreements, mortgages" into a new spreadsheet with doc numbers
- User asks for a counsel-ready list of open encumbrances + outstanding
  documents for a land parcel set

## Key Steps (summary)

1. Dump all tabs via Sheets `batchGet` (NOT per-tab `get` — 60 reads/min quota)
2. Classify every transaction row chronologically per survey (see table in
   the reference)
3. Carry over survey-level flags the transaction tab omits (OPEN DTD,
   dropped txns, zero-txn parcels, no sale deed)
4. Build 4-tab openpyxl workbook: Pending Register, Survey Issues, Open
   Mortgages (RED), Full Ledger
5. Upload twice: Google Sheets conversion + native .xlsx copy; verify readback

## References

- `ec-transaction-register-extraction.md` — full workflow:
  batchGet rate-limit fix, per-document classification table, the 4-tab
  openpyxl register shape, Drive delivery as Google Sheet + xlsx, and
  dedup / short-vs-full-doc-no / parties-split / scope-re-slicing pitfalls.

## Related

- `property-title-due-diligence` (umbrella) — RTC/EC/khata reading, title
  chain, survey-wise inventories. This skill is the EC-register-specific
  extraction piece.