# TN Reginet EC — Multi-EC Transaction Parsing (per-survey tables + master grouping)

Worked example 2026-08-13: 5 ECs (Sy 158, 166, 167, 176, 177) filed against
individual survey numbers in Sevaganapalli (Hozur SRO → Bagalur SRO, search
period 1975–2026). 170 entries, 131 unique registered documents, delivered as
an openpyxl workbook then mirrored as new tabs in the DocMatrix spreadsheet.

## When to use

- User uploads several TN Registration Dept EC PDFs (one per survey number)
  and asks to "verify all transactions", "list transactions per survey no",
  "generate a spreadsheet" with Sl No / Sy No / Sub-number / Type / Date /
  From / To / Doc No — and dedupe documents that span multiple survey nos.

## Extraction source: pdftotext -bbox, NOT pdfplumber

- TN Reginet ECs have a real text layer (no OCR needed) but use a legacy Tamil
  font: **pdfplumber returns garbled Tamil**, while `pdftotext` renders Tamil
  correctly with preserved columns.
- Use `pdftotext -bbox input.pdf out.xml` as the parser input: correct text +
  per-word x/y coordinates. Column classification by **x-coordinate** is stable
  across the compact vs expanded entry formats that shift character columns:
  executant words ≈ x 414, claimant words ≈ x 546 (pdftotext bbox units).

## Parser structure that worked

1. **Line grouping: discrete y-bucket clustering.** Running-average cluster
   merges everything into one block. Bucket lines whose y0/y1 fall within a
   tolerance (coarsen until same-row words stay together). Track `<page>`
   boundaries explicitly — the `<page width=...>` tag has NO `number` attribute;
   carry a page counter yourself.
2. **Entry-start detection: Sr-line candidates are kept ONLY if the following
   block contains a doc number + a "Consideration Value" line.** A look-ahead
   that just checks "next line has numbers" backfires (grabs junk). The
   doc-no + "Consideration Value" filter is the reliable gate.
3. **Survey extraction:**
   - Modern entries parse "Survey No-Extent" lines.
   - Old format: the Tamil label "புல எண்" (survey no.) sits on its OWN line
     above the number — relax the regex to tolerate that.
   - **Continuation lines: a line must contain at least one survey token with
     `/` to be accepted as a survey continuation** (prevents boundary text and
     extent numbers from leaking in). Then ALL tokens on that line are surveys.
   - **Boundary descriptions (எல்லை விபரங்கள்) bleed into survey lists** —
     neighboring-plot refs like 176/285, 176/2B4B are boundary neighbors, NOT
     transaction surveys. Hard-stop survey collection at the boundary section.
   - Modern continuation lines can carry "Property Type" / "Village" labels in
     the LEFT zone while the survey list is in the RIGHT zone of the same line —
     check the right zone only, never the full-line text.
4. **Consideration:** stop the scan at Schedule lines; take only the first real
   value line. Modern entries use "Rs." format on the value line.
5. **Names:** trailing standalone page-number artifacts (e.g. "35") bleed into
   party names — clean them. First executant can sit on the line ABOVE the Sr
   marker (PDF baseline/page-break quirk) — look one line above.
6. **Post-parse noise filter:** with boundary prose excluded, only 1-digit
   artifacts need dropping (2-digit whole surveys like 39, 96, 104, 111 are
   legit and must survive). Pure-digit extent lines ("08", "10–17", "19–23")
   leak if the slash-gate is missing.

## Verification — count parity with EC footers

Each EC footer states the entry count. Parse must match EXACTLY:
`158: 52, 166: 35, 167: 15, 176: 29, 177: 39 = 170`. Any mismatch = parser
regression, not an EC anomaly. Also spot-check parties/dates/doc numbers
against raw PDF lines.

## Master-document grouping (dedupe across ECs)

- 131 unique registered docs from 170 entries; 29 docs appear in 2+ ECs.
- Per-survey tabs: Sl No | Sy No | Sub-number(s) | Type | Transaction date |
  From (executants) | To (claimants) | Doc No | **Other Sy Nos in same doc** |
  Consideration | PR No.
- Master tab: each unique doc ONCE, with "All Survey Nos in this doc (grouped)"
  + "Appears in ECs" column.
- **Same doc shows slightly different survey lists per EC due to page-break
  truncation — take the UNION across ECs for the master list.**
- Multi-EC exemplars: 9188/2025 gift deed (all 5 ECs, 19 surveys incl.
  158/1C9A·1C9B, 166/1·2B2·3A–3F, 167/1G·2C·2D, 168/1B, 176/1B2D·2B4A,
  177/1A1A·1A1B), 22229/2023 partition (4 ECs), 7049/2025 mortgage (3 ECs).

## Workbook delivery

- openpyxl in a uv venv (`/opt/data/.venv/bin/python`); the system python
  lacks openpyxl. Load with `data_only=True` and dump each sheet to JSON
  before pushing to Sheets (avoids re-reading xlsx twice).
- When the user later says "add this sheet to <spreadsheet>": create NEW tabs
  via `spreadsheets().batchUpdate` addSheet, write via
  `values().batchUpdate` (RAW), then **read back and verify row counts**.
  Bold+freeze headers, color-code status columns, autosize. NEVER touch
  existing tabs — "add as new sheet, don't change anything".
