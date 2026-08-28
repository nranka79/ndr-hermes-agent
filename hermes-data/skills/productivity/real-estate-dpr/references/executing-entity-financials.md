# Executing-Entity Financials in DPR Section 1.3

When the user asks to "add entity financials for the executing entity for all project DPRs", the
task is to ensure each DPR's Section 1.3 shows the financials of the **project's executing
entity** — NOT just DRA Realty (the group company table that is often the default placeholder).
Worked 25-Aug-2026 across the 4 Ranka DPRs.

## DRA Ranka executing entity map (verified Aug-2026)

| Project | Executing entity | PAN | Notes |
|---|---|---|---|
| Udaya | DRA Thindlu Land Partners | AAXFD2296G | firm formed Sep-2024 → only 2 FYs of ITR-5 |
| Amber | DRA Realty Pvt Ltd | AAPCS9730H | executing entity IS the group company → no entity swap needed |
| Oasis | DRA Realty + Seveganapalli Land Partners | AFCFS4430H (SLP) | add the SLP block (company table already present) |
| NorthStar | DRA Ranka Holdings | AARFD2916M (NOT "AADFD7789F1Z") | see PAN-correction warning below |

The naive DPR has Section 1.3 = DRA Realty's 6×4 ITR table only, with a stale line
"ITRs of the partnership firms ... extraction in progress". The fix per project:
- Amber: nothing to add — its executing entity is DRA Realty; the 6×4 table titled
  "Executing Entity Financials" is already correct. Re-title/confirm, don't duplicate.
- Udaya / Oasis / NorthStar: add the partnership firm's own financial block.

## Where the firm financials live on Drive (firm-doc folders)

Drive-wide search `name contains 'firm related'` and `name contains 'print'` finds them:
- Seveganapalli Land Partners: `1UfuXj5Fry_qFQ5uqsow88LqE9ntxydZp` (ITR-5 forms, PAN, GST,
  reconstitution acks)
- DRA Thindlu / other firms: `1u7tPOk_hrafr0bYXSh0XAeSlg290l1Bw` ("Firm Related Documents")
- Firm dossiers (`*_Dossier.docx`) carry the *partner/registration profile* but explicitly note
  when ITRs are NOT found — read them first to know what exists.
- Entity PAN/GST/registration live in the dossier + KYC PDFs, not always in the DPR (often stale there).

When hunting any entity's ITRs, search these patterns across Drive (they appear once per entity):
`name contains 'Form_pdf'`, `'<ack-number>'`, `'<PAN>'`, `'Statement of Income'`, `'Computation'`.
ITR-5 forms usually split into: Acknowledgement PDF (small, has total income + loss + ack no),
Form_pdf (large, full return incl. balance sheet), Statement_of_Income + Computation PDFs (clean
P&L summary), and a `*_Dossier.docx`.

## Extracting figures from ITR-5 (partnership) forms

Balance-sheet position is the lender-facing value-add beyond the income table. Use
`pdftotext -layout` (ITR-5 forms are text-layer PDFs, NOT scanned):
- **Partner's Capital** (PART A-BS line `1a`), **Unsecured loans** (`2biiD`/"from others"),
  **Total Sources = 1c+2c** (`5`), **WIP / Stock-in-trade / Inventories** (`iB` Work In Process =
  land under assembly), **Cash & bank** (`iiiD`), **Advances recoverable** (`bi`).
- P&L: **Net Profit before taxes** (`54`), Total Income (`1A` on ack), current-year business loss
  (ack line 1).
- Partner schedule: change/admitted/retired table gives the % share and reconstitution dates;
  year-end "as on 31-Mar" table gives the current partner ratio.

For partnership firms the entity's capital is often small/near-zero and the real funding sits in
**unsecured loans from group/related parties** deployed into **land held as work-in-progress** —
state that narrative explicitly ("pre-revenue land-assembly phase; loans are group/partner funding
into land holdings"). This is normal for land-holding SPVs and banks expect to see it.

## HONEST-FLAG RULE (never fabricate)

If an entity has NO ITRs on Drive (verified across dossier + all project folders + Form_pdf search),
DO NOT invent figures. Add the entity profile (formation, PAN/GST, partnership evolution,
reconstitution) + a clear "ITR / audited financials: NOT AVAILABLE as of <date> — to be sourced
from the firm/CA and appended" + the document set on file. Leave a discoverable hook so the figures
slot in when supplied.

## PAN-correction warning

The DPR's Section 1.2 registration line for DRA Ranka Holdings carried a garbled
"PAN AADFD7789F1Z; GST 29AADFD7789F1ZD". The actual values (from the PAN-card image + GST REG-06
certificate) are **PAN AARFD2916M, GST 29AARFD2916M1ZU**. Always verify entity PAN/GST from the
source KYC document (vision_analyze the PAN card image, pdftotext the GST cert) before trusting a
DPR's registration line — malformed PANs are common in drafted packs.

## Docs-API insertion recap (see docs-api-financial-tables.md for the full recipe)

Split into batches with a fresh `documents().get` between each: cell-fills first (ascending,
`cell.startIndex + 1`, running delta), then profile paragraph before Table A at
`tA.startIndex - 1` (the `\n` paragraph preceding the table), then source note after Table B at
`tB.endIndex`. There is NO `insertParagraph` request — paragraphs come from `insertText("\n")`.
Stale "extraction in progress" line: `deleteContentRange` then `insertText` at the same start index.
