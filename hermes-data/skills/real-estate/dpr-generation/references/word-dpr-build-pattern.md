# Word DPR Build Pattern (python-docx, DRA-branded)

Session-proven recipe (24-Aug-2026). User rejected slides and mandated **Word (.docx) format only** for DPRs. This reference captures the working generator structure, branding assets, and pitfalls.

## Verified DRA brand assets (under psingh's google-draas)

| Use | File ID | Notes |
|---|---|---|
| Cover logo (JPG, white bg) | `1MgYvRuk8WowJ1tpUg9nmXlxbgJe8a_Xo` | DRA wordmark + gold flame + "PROJECTS PVT LTD" — clean on white, use in Word covers |
| Logo PNG (black bg) | `1YIDxTeAVhrxtllKVkAZ72574lix-EkS3` | Wood-grain/brown on black — NOT suitable for covers |
| ~~Logo folder~~ | `1yFyicxHzsL2IAdZQxnmm6d03aMRqJhw6` | 404 under psingh (stale; belongs to ndr's session) |
| ~~Logo JPG~~ | `15_mFlZ50njw2jrlquDHCQnczYjOARZAa` | 404 under psingh (stale) |

Also confirmed "DRA Logo.jpg" alternatives found by `name contains 'DRA' + image mimeType` search; always `vision_analyze` before embedding — some files in the search are unrelated (site/drain photos).

Palette: charcoal `#231F20`, gold `#F7B519`, cream `#FDF5F2`, grey `#3E3E3D`, light row `#F5F0EA`.

## Generator structure (10-section lender DPR, A4)

- Cover: centered logo → "DRA — HOME OF PRIDE" → gold bottom rule (w:pBdr w:bottom sz=30 F7B519) → DETAILED PROJECT REPORT (26pt charcoal) → project name (30pt) → type (14pt grey) → gold rule → centered meta (entity / location / status / prepared by / date) → charcoal 1-cell CONFIDENTIAL bar table.
- Contents page → Executive Summary → sections 1–10 (template in `references/dra-dpr-template-sections.md`).
- h1: 16pt bold charcoal + gold bottom border; h2: 13pt bold charcoal.
- Tables: `Table Grid` style, autofit; header row bg `231F20` cream bold text; even body rows `F5F0EA`; font 8–10.
- Red-italic `[ to be provided ]` placeholders for anything unknown (cost heads beyond confirmed totals, contractor profiles, IRR/DSCR/NPV, approval statuses) — never fabricate.
- Annexures: bullets + live hyperlinks (python-docx has no native hyperlink; use `part.relate_to(url, ..., is_external=True)` + manual `w:hyperlink`/`w:r` XML with color 1155CC).

## Key helpers (patterns)

- `set_cell_bg(cell, hex)`: append `w:shd` to cell tcPr (val clear, fill hex).
- `add_hyperlink(paragraph, url, text)`: relate_to external + build `w:hyperlink > w:r > w:rPr(color)+w:t`.
- Gold rule: paragraph with `w:pBdr/w:bottom` (single, sz 30, F7B519).

## Financial model parameters baked into generated tables (user-confirmed 24-Aug-2026)

- Interest 11% p.a., tenor 72 months; sales velocity 30+10+10+10+15+15 over 24+6 months + 10% retention; start = Q2 (assumed).
- Financing rule: land owned by developer → land value = equity; 25% of dev cost = capital equity; 75% = debt.
- Amber: equity ₹4.0 Cr (goodwill 1 + IFRSD 1 + NDR ~2, all treated as equity) / debt ₹6.7 Cr; CAS saleable 27,543.25 sq.ft.
- Udaya: 38 plots @ ₹4,000/sq.ft → ₹18.58 Cr sales; land equity ₹6.1 + cap equity ₹0.85 + debt ₹2.55.
- Oasis: Phase 1 = 7.53 ac ONLY (owned 6.58 + JDA 0.95); land equity ₹37.51 (6.58 ac @ ₹5.70 Cr/ac) + 25% ₹46.45 + debt ₹139.35 = ₹223.31 total; sales ₹345.26 Cr (investor sheet Phase I rows).
- NorthStar: JDA 67:33, no land equity; cap equity ₹8.85 + debt ₹26.55.
- Quarterly cash flow: debt = 75% of quarterly spend (milestone-linked); interest on opening balance at 11%/4.
- Balance sheet: year-end, Surplus plug = assets − debt − equity so it balances (negative = absorbed interest cost).

## Pitfalls hit during the build

1. **Param shadowing** — name the project dict param `proj` from the start; `p = doc.add_paragraph()` silently shadows `p` and breaks `p['key']` with "Paragraph object is not subscriptable". Must rename in the function signature AND every helper call site (exec_summary, cost_breakdown, cashflow_model, bal_sheet).
2. **Filename interpolation** — `Ranka_{key}_DPR.docx` from a dict key yields `Ranka_RANKAAMBER_DPR.docx`. Derive from the project name.
3. **body() helper needs explicit `bold=False` param** if you want bold note text.
4. **`key` not defined in save path** — the save line inside build_dpr must use the project dict, not an outer scope variable.
5. **Missing fields** — `price_psf`, `note`, `comp_rows`, `positioning`, `annex_links` are per-project; populate them in a runner script before calling the generator (don't rely on the base data JSON).

## Verification before shipping

Re-open each .docx with python-docx: assert all 10 section headers present in paragraphs, count tables (~19 expected), spot-check first (cover) and last (annexure links) paragraphs. Then upload as DOCX mimeType to a fresh folder with `anyone -> writer` share so the user can edit from any account.

## Related

- Slides conversion (if ever requested again): Slides API is disabled → build .pptx (python-pptx), upload with `mimeType: application/vnd.google-apps.presentation` to auto-convert. See `docs-api-financial-tables.md`.
- DPR folder from prior sessions may live under ndr's account and 404 under psingh — rebuild from investor spreadsheet rather than chasing the missing folder.