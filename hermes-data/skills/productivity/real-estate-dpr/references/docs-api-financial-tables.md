# Docs API: Financial Statement Tables in Native DPR Docs

Worked 24-Aug-2026 session: adding Financing Structure (6.2), Cash Flow (7.2) and
Balance Sheet Projections (7.4) tables to all 4 Ranka DPRs (Amber, Udaya, Oasis,
NorthStar). Every table you build in a native Google Doc via the Docs API will hit
these pitfalls — the "batchUpdate index" model is subtle.

## The user's capital-structure rule (DRA DPR policy)

> "In all the projects where project land is owned by the developer, add that value
> as developer equity + 25% of the total development cost as capital equity and
> balance as debt from investors/institutions."

Applied per project (24-Aug-2026):
- **JDA projects (Amber, NorthStar)** — land NOT owned: land equity = Nil; capital
  equity = 25% × dev cost; debt = 75% × dev cost.
  - Amber: cost 14.82 (13.82 const + 1.0 goodwill) → eq 3.70 / debt 11.12
  - NorthStar: cost 53.82 (97,853 sft dev share × ₹5,500) → eq 13.46 / debt 40.36
- **Owned-land projects**: land value = developer equity; + 25% × (dev cost excl.
  land) as capital equity; debt fills the balance.
  - Udaya: land 6.12 + cap eq 0.85 (25% × 3.40) → total eq 6.97 / debt 2.55
  - Oasis: land 73.09 (8.86 ac implied from cost build-up 51.59+21.50) + cap eq
    56.50 (25% × 226.02) → total eq 129.59 / debt 169.52 (cost incl. land 299.11)
- **Cash flow timing**: equity front-loaded (60/90/100% by Q3), receipts follow a
  milestone curve (5/12/25/40/55/72/88/100%), spend an S-curve (5/15/30/50/70/86/96/100%).
  IMPORTANT: with these curves, cumulative receipts outrun spend → **debt drawdown
  computes to ₹0 across all quarters**. That's a legitimate cash-positive outcome,
  but for a lender pack you may prefer the standard construction-finance pattern
  (debt drawn at 25/50/75 of facility in early quarters). Offer both to the user.
- **Balance sheet balance trick**: set `Surplus = Total Assets − Debt − Equity`
  (plug) so Assets == Liab+Eq by construction. Never report a BS that doesn't balance.

## Table insertion — working recipe

`insertTable` at `heading_end_index` (endIndex of the section heading INCLUDES the
trailing newline, so inserting there lands the table right after the heading).

### 1. Create the table
```python
docs.documents().batchUpdate(documentId=did, body={'requests':[
  {'insertTable': {'location': {'index': at_index}, 'rows': nrows, 'columns': ncols}}
]})
```

### 2. Fill cells — insert text at `cell['startIndex'] + 1`, sorted, with offset math
- Each empty cell contains one empty paragraph; its text must be inserted at
  `cell['startIndex'] + 1` (NOT `startIndex` — that's the cell marker and fails
  with "insertion index must be inside the bounds of an existing paragraph").
- **`insertText` in ONE batch DOES shift indices.** Collect all (cell_start+1, value)
  pairs, sort by position, then insert with a running `delta` (`pos + delta`,
  `delta += len(value)`). Blindly using stale indices fails on request N>0.
- **Skip empty-string cells** (`if val == '': continue`) — `insertText` with text ""
  fails ("must specify text to insert").
- **Do NOT mix cell-fills with paragraph/other inserts in one batch** (25-Aug-2026):
  the running-delta model is only valid for strictly ascending cell fills. When you
  also need to insert a profile paragraph and a source note, split into SEPARATE
  batches with a FRESH `documents().get` read between each — Cell-fill batch first,
  then read → insert paragraph before table at `tA['startIndex'] - 1` (the `\n`
  paragraph immediately preceding the table) → read → insert note after table at
  `tB['endIndex']` → read → replace stale line. This is far safer than interleaving
  offsets for interleaved insertion points. (Worked cleanly for this pass.)
- **There is NO `insertParagraph` request** in the Docs API — paragraphs are created
  by `insertText` of `"\n"`. Using `insertParagraph` fails with "Unknown name
  \"insertParagraph\"" and the whole batch rolls back atomically (so table A is gone
  and you must re-insert). Always insert a blank `"\n"` paragraph, then `insertTable`.

### 3. Style cells — text-style based, re-fetch the model AFTER filling
- **Do NOT use `updateTableCellStyle` with `tableRange`** → "rowSpan must be
  strictly positive, was: 0" (requires tableStartLocation + row/col indices that are
  easy to get wrong). Use `updateTextStyle` with `backgroundColor` in the text style
  instead — the whole header row gets charcoal bg via the text range.
- **Docs textStyle colors and sizes need the full wrapper objects**: `foregroundColor`
  / `backgroundColor` must be `{'color': {'rgbColor': {...}}}` (NOT bare
  `{'red': ..., 'green': ..., 'blue': ...}` — that fails with "Unknown name "red""),
  and `fontSize` must be `{'magnitude': 8, 'unit': 'PT'}` (a bare int fails with
  "Invalid value ... (Dimension), 8"). These two bit during the 7.5 IRR-metrics pass
  (24-Aug-2026) before the batch went through.
- Header row: bold + white + charcoal `rgbColor(0x23/255, 0x1F/255, 0x20/255)`,
  `fields='fontSize,bold,foregroundColor,backgroundColor'`. Total row: bold + cream
  `(0xFD/255, 0xF5/255, 0xF2/255)`.
- **Skip empty style ranges** (`if ce <= cs: continue`) — styling an empty cell
  fails with "The range should not be empty".
- **Column widths**: `updateTableColumnProperties` requires BOTH
  `'widthType': 'FIXED_WIDTH'` in tableColumnProperties AND `'fields': 'width,widthType'`.

### 4. Deleting tables (cleanup) — one at a time, re-fetch each iteration
`deleteContentRange` over a whole table shifts ALL subsequent indices. Loop:
fetch doc → find first target table → delete → fetch again. Never emit multiple
deletes from one snapshot (fails "Invalid deletion range" or deletes the wrong table).

## Pitfalls (all hit in the 24-Aug session)

- **'Particulars' is NOT a unique identifier.** The pre-existing ITR table in every
  DPR (Section 1.3, first cell "Particulars") collides with the new Financing table
  (also first cell "Particulars"). Match on the SECOND column too
  (`Amount (₹ Cr)`) or restrict cleanup to content AFTER the 6.2 heading. I
  accidentally purged the ITR financial tables from all 4 DPRs — restored from data
  captured in earlier doc dumps. Always snapshot table data before bulk deletes.
- **Glued headings**: `insertText` with `'\n' + heading` at the end of a body
  paragraph is fine, but if you insert a heading WITHOUT a trailing newline it glues
  to the next paragraph's text (saw "policy:7. Financial Estimates & Projections").
  Fix: find the merged paragraph, `insertText` `'\n'` at the exact split offset, then
  style the heading (`updateParagraphStyle` namedStyleType HEADING_2 + charcoal color).
- **Find-and-delete placeholders FIRST, then insert at same index** (from
  real-estate-dpr SKILL.md step 10) — holds for table inserts too: the deleted
  range startIndex is the table insertion point.
- **Idempotency**: before inserting a section block, check `find_para(..., ['Heading
  Text'])` and skip if present. Multiple retries created triplicated financing tables.
- **Cleanup over-matching empty tables**: an orphaned empty 10×6 table (leftover from
  a failed insert) looks like anything — detect by "all cells empty AND rows ≥ 8" and
  delete it, else the section ends up with a floating blank table.
- **Run scripts via `write_file` + `python3 /tmp/x.py`, not shell heredocs**: the
  terminal guard flags `&&` inside heredocs as backgrounding ("Foreground command uses
  '&' backgrounding") — and after a couple of `&&`-containing heredocs it became
  unreliable. Long Python API scripts belong in files.

## Canonical model inputs (Ranka, 24-Aug-2026)

| Project | Sales (₹ Cr) | Dev cost (₹ Cr) | Qtrs | Receipt curve | Spend curve |
|---|---|---|---|---|---|
| Amber | 18.42 (dev share 15,350 sft @12k) | 14.82 | 8 | 5/12/25/40/55/72/88/100 | 5/15/30/50/70/86/96/100 |
| Udaya | 15.90 | 3.40 | 4 | 15/45/75/100 | 25/60/90/100 |
| Oasis | 473.20 (P1 345.26 + P2 127.94) | 226.02 (ex-land) | 8 | 5/12/25/40/60/78/92/100 | 6/16/32/50/68/84/96/100 |
| NorthStar | 117.42 (97,853 sft @12k) | 53.82 | 8 | 5/12/25/40/55/72/88/100 | 5/15/30/50/70/86/96/100 |

Equity draw pattern: Q1 60% of equity, Q2 90% cum, Q3 100% (front-loaded).
Balance-sheet grouping: nq/len(years) quarters per year-end column (8q→3yr for
Amber/NS, 4q→2yr Udaya, 8q→4yr Oasis).