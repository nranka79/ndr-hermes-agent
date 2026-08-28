---
name: dpr-generation
description: "Generate Detailed Project Reports (DPRs) for DRA / Indian real-estate projects for lender appraisal. Pull per-project financials from the DRA Investor Portfolio spreadsheet, statuses from the firm-dossier checklist, and annexure links from project folders; build a branded DRA-template Google Doc pack; update DPR sections in place via the Docs API."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# DPR Generation (Detailed Project Report)

Use when the user asks for a DPR / Detailed Project Report / lender-appraisal pack for a real-estate project (Ranka Amber, Ranka Oasis, Ranka Udaya, Ranka North Star, Byadarahalli, etc.) — "prepare DPR", "DPR for each project", "project finance document".

## Data sources (DRA)

- **Investor Portfolio spreadsheet** `1wDKS0SxtY0EF_-JUe2BfXzLSSwh4J5fo4y0sI_brFfw` — canonical per-project financials. One tab per project + a `Project Summary` tab. Tab schema (entity/land/specs/sharing/units/approvals/profitability/sales) is documented in `references/investor-portfolio-schema.md`.
- **Firm Dossiers Master (PS)** `1rb9h7PZczba0kTDTjxkNM0ET1XW-eiuIUYrwHHRuuVs` — entity KYC, financials, "Required Documentation Checklist" tab (project-wise approval/status tables, all Drive links verified).
- **Project folders on Drive** — annexure PDFs (sale deeds, ECs, legal opinions, brochures). Always resolve REAL file IDs, never filename-only references.
- **Enterprise Data sheet** `1HqvqLFwtK45UZWyzChwyGf25I8Bb4EW2qcYxII76xyI`; **group deck** `1qxnizk6GzT5xGG8M45FXjKCHpDkI7ac2` (DRA Portfolio PDF).
- **Pricing/competitor research**: per-project R&D decks exist on Drive — see `property-pricing-sources/references/ranka-project-pricing-rnd-index.md`; reuse before re-searching.

## Workflow

1. **Inspect portfolio spreadsheet**: read each project tab + Project Summary (FORMATTED_VALUE). Capture land, units, saleable area, sales value, cost, profit, margin, approvals, sales detail.
2. **Check the checklist workbook** for the project's approval statuses & verified links (approvals table in the DPR comes from here).
3. **Inventory the project folder** for annexure documents; capture real file IDs (e.g. search folder for 'Brochure', 'Legal', 'EC').
4. **Build the .docx** with python-docx (branded DRA template): logo cover (**verified logo JPG `1MgYvRuk8WowJ1tpUg9nmXlxbgJe8a_Xo`** — the old IDs `15_mFlZ50njw2jrlquDHCQnczYjOARZAa` and folder `1yFyicxHzsL2IAdZQxnmm6d03aMRqJhw6` 404 under psingh; `1YIDxTeAVhrxtllKVkAZ72574lix-EkS3` is a black-bg variant, not suitable for covers; palette charcoal #231F20, gold #F7B519), gold rules, charcoal headings, shaded table headers, hyperlink helper, Contents page, CONFIDENTIAL bar. Full recipe in `references/word-dpr-build-pattern.md`.
5. **Deliver as WORD .docx — user-mandated format (24-Aug-2026)**: user rejected the slide-deck DPR structure ("I AM NOT HAPPY WITH THE STRUCTURE OF THE DPR... RE-GENERATE FOR EACH PROJECT IN A WORD FORMAT ONLY"). DPR deliverable = .docx only; upload with DOCX mimeType to a new Drive folder owned by the session account, share `anyone -> writer`. Do NOT auto-convert to Google Docs unless the user explicitly asks. If a native Google Doc IS requested: `drive.files().create(body={'name':..., 'mimeType':'application/vnd.google-apps.document','parents':[folder]}, media_body=MediaFileUpload(path, mimetype=DOCX_MIME))` — the import converts tables/colors/logo. NOTE: prior DPR folder `1eh_t3wKkiYmGFm4wCGcVqurc6D7mz1IY` 404s under psingh's token (created under ndr's account) — search by name / sharedWithMe, don't block on it.
6. **Verify**: export text/plain → check all 10 sections + competitor block; export PDF → pdftoppm page 1 → vision_analyze for logo/colors.
7. **In-place edits later** (e.g. filling a placeholder section): Docs API — find the placeholder paragraph, `deleteContentRange`, then `insertText`. Never `files().update()` with docx media on a native Google Doc (mimeType can't change). Reusable script: `scripts/dpr_google_doc_update.py`.

## DRA DPR template (10 sections)

Executive Summary · 1. Developer & Promoter Profile · 2. Project Description & Scope · 3. Regulatory Approvals & Statutory Clearances · 4. Technical & Engineering Aspects · 5. Project Cost & Means of Finance · 6. Financial Estimates & Projections · 7. Market Analysis & Commercial Viability · 8. Risk Analysis & Mitigation Plan · 9. Security & Collateral Proposed · 10. Annexures & Enclosures. (Order changed 25-Aug-2026: Cost & Financials moved BEFORE Market Analysis; DPRs + Master Template reordered/renumbered in place — subsection renumber map: 6.x→5.x, 7.x→6.x, 5.x→7.x.) Full field-level template in `references/dra-dpr-template-sections.md`.

## Executing-entity financials block (Section 1.3)

Every DPR carries a **Section 1.3 (Financials / Financial Soundness / Executing Entity Financials)** with a DRA Realty ITR summary table (6×4) — but the DRA Realty block only belongs where DRA Realty is the executing entity or a partner. DPR→entity mapping (verified Aug-2026):

- Amber → **DRA Realty Pvt Ltd** (executing)
- Oasis → executing entity 1 = DRA Realty + **Seveganapalli Land Partners** (95% DRA Realty partner)
- Udaya → **DRA Thindlu Land Partners** (DRA Realty 51% partner)
- NorthStar → **DRA Ranka Holdings** (partners are Ranka family ONLY: Manish 71.25% / NDR 21.25% / Mamata 7.50% — DRA Realty is NOT a partner; its ITR table is still shown as promoter financials)

When the user asks to add an entity's **Balance Sheet Position as at 31st March**, insert an 11×4 audited table right after that entity's ITR table (before the "Audited documents:" paragraph): Share Capital · Reserves & Surplus · Short-term Borrowings · Provisions & Other Liabilities · Total Liabilities · Fixed Assets · Non-current Investments · Cash & Bank · Advances & Other Current Assets · Total Assets, with a bold "… — Balance Sheet Position as at 31st March (audited):" label and a source note naming the auditor + statement dates. Full recipe, INSERTION SEQUENCE that works (label→table→source→fill descending), source PDF locations on Drive, and the verified DRA Realty numbers: see `references/executing-entity-financial-blocks.md`.

Rules learned the hard way:
- **FUZZY "AS ON 31ST MARCH" ask = the 3 audited FYs already in the ITR table** (FY22-23/23-24/24-25 for DRA Realty), NOT just the latest year — mirror the ITR table's columns.
- **If FY25-26 audited statements don't exist on Drive, say so and cap the table at the last available year** — never extend or invent.
- **DRA Realty audited statements are poor-contrast scans** — use the enhanced-contrast OCR recipe (`ocr-and-documents`): pdftoppm -r 250 -gray → PIL autocontrast(cutoff=1)/Contrast 1.6/Sharpness 1.5 → tesseract --psm 6 → locate BS pages by keyword (BALANCE SHEET/EQUITY AND LIABILITIES/ASSETS). Works; plain render+psm does not. Note "Rupees in Thousands" header — ×1000 before quoting ₹.
- **Reconcile totals** (assets = liabilities) before writing to the DPR; flag sub-₹1K rounding only.

## Pitfalls

- **Never fabricate financial metrics.** IRR / DSCR / NPV / break-even go in as red-italic placeholders ("to be computed from financial model") until a real financial model exists. Same for competitor benchmarking if research not yet found — but first SEARCH Drive for the project's own pricing R&D deck.
- **Sheet date cells are Excel serials** (40644 ≈ mid-2011; 45906 ≈ mid-2025). Format them, don't pass through raw.
- **Export-blocked Drive files (403 "Export on...")**: decks/maps shared with download-disabled settings can't be exported via API. Pivot: session_search for the deck-creation session, or live portal mining (NoBroker) via `property-pricing-sources`.
- **Filename-only references ≠ links** (e.g. "Ranka Udaya Brochure.pdf.pdf" as text). Search the project folder for the actual PDF before marking missing.
- **Replacing old docs**: trashing is reversible (30-day Drive trash); upload new set with same folder before/after trashing old ones.
- **Verify link health** before shipping: run the workbook link-audit pattern (`google-workspace/references/sheets-workbook-link-audit-and-restructure.md`) so annexures never carry 404s.
- **Verifying "have you updated the files?": a body text dump MISSES table cells.** `documents().get()` paragraph-walking does not descend into tables. Always extract tables with the recursive `table > tableRows > tableCells` walker in `references/docs-table-verification-and-cleanup.md` before claiming metrics are/aren't populated.
- **Stale placeholder sentence can survive alongside a populated table.** After filling Section 7.5 with real IRR values, a leftover narrative sentence ("DSCR, Project IRR and NPV are to be computed...") can remain earlier in the doc body and contradict the populated table. When replacing placeholders, grep the WHOLE doc for the stale phrase and delete it too (re-scan fresh start/end indices before each `deleteContentRange` — indices shift after edits). See `references/docs-table-verification-and-cleanup.md`.
- **Auth**: always `HERMES_SESSION_USER_ID=psingh` + `service_name='google-draas'` for PS's Drive work; verify identity if a doc 404s.
- **python-docx param shadowing trap**: inside the DPR generator, name the project-dict param `proj`, never `p` — `p = doc.add_paragraph()` shadows the dict param and `p['key']` then throws `'Paragraph' object is not subscriptable` (cost 4+ debug cycles on the Word-DPR run; rename param + ALL call sites in helpers like exec_summary/cost_breakdown/cashflow_model/bal_sheet).
- **Filenames**: derive from project name, e.g. `RANKA_AMBER_DPR.docx` — interpolating `{key}` from a dict key produces `Ranka_RANKAAMBER_DPR.docx` ugliness.
- **Word format = only format unless told otherwise** (user, 24-Aug-2026): slides were the wrong deliverable; DPRs ship as branded .docx, red-italic `[ to be provided ]` placeholders for unknown cost heads/IRR/DSCR/NPV. Verify by re-opening each .docx with python-docx and asserting all 10 section headers + table count.

## References & scripts

- `references/investor-portfolio-schema.md` — exact tab layout & per-project key fields of the DRA Investor Portfolio spreadsheet.
- `references/dra-dpr-template-sections.md` — the 10-section DPR template with field-level content.
- `references/docs-api-financial-tables.md` — **worked 6.2/7.2/7.4 tables for all 4 Ranka DPRs**: user-mandated financing rule + confirmed parameters (11%/72 mo, velocity 30+10+10+10+15+15, Q2 start, Amber goodwill/IFRSD = paid equity, Udaya ₹4,000/sqft), Oasis **Phase 1 = 7.53 ac** scoping rule, Amber CAS saleable area (27,543.25 sq.ft), Docs API table-insert mechanics (startIndex+1, idempotent inserts, Surplus plug, purge-discipline caution), DPR→editable-slides pivot (Slides API disabled → pptx → Drive convert), image-ownership pitfall.
- `scripts/dpr_google_doc_update.py` — Docs API placeholder replacement (find paragraph → delete → insert), used for filling Section 5.2 etc.
- `references/word-dpr-build-pattern.md` — **Word-format DPR generation** (user's mandated format): python-docx branded generator structure, verified logo file IDs (old ones 404), gold-rule/hyperlink/cell-shading helper patterns, model parameters baked into 6.2/7.2/7.3/7.4 tables, and the param-shadowing + filename pitfalls.
- `references/executing-entity-financial-blocks.md` — **Section 1.3 executing-entity financials blocks**: DPR→entity mapping, verified DRA Realty BS-position numbers (FY22-23→24-25), insertion sequence (label→table→source→descending fill), source PDF Drive IDs, OCR recipe for the poor-contrast scans.
- `references/docs-table-verification-and-cleanup.md` — **verifying DPR content & cleanup**: recursive Docs-API table extractor (body-text dump misses table cells), whole-doc stale-placeholder scan + `deleteContentRange`, Drive parent-chain location walk, and duplicate-folder trash-safe cleanup.

## Pitfalls (financial tables)

- **Oasis financials are Phase 1 ONLY (7.53 ac)** — the approved layout basis. Do NOT model on the full 8.86/10.31 ac land holding. User corrected this explicitly (24-Aug-2026); all 6.2/7.2/7.4 numbers must come from the investor sheet's Phase I rows.
- **Amber saleable area comes from the Customer Area Statement** (27,543.25 sq.ft per SSA) when the user asks for "saleable area as per customer area statement" — it differs from the portfolio sheet's 30,700 built-up / 28,900 FAR.
- **Slides API is disabled on the GCP project** — convert DPRs to editable decks by building branded .pptx (python-pptx) then Drive-uploading with `mimeType: application/vnd.google-apps.presentation`. Verify via export→PDF→pymupdf. See `references/docs-api-financial-tables.md`.