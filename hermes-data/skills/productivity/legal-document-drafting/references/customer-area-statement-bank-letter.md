# Customer Area Statement for Bank Pre-Approval — DRA Realty letterhead docx

Session-proven pattern: portrait covering letter + landscape Annexure-A unit-wise Customer Area Statement, generated with python-docx. Reusable for Ranka Amber and similar DRA project pre-approval letters.

## Area statement spec (customer-facing, RERA-aligned)

| # | Area Type | What to furnish |
|---|-----------|-----------------|
| 1 | RERA Carpet Area | Net usable floor area incl. internal wall thickness; excl. external walls, balcony/verandah, open terrace |
| 2 | Exclusive Areas | Balcony, Utility/Wash, Exclusive Open Terrace — listed separately from carpet |
| 3 | Covered / External Walls | Outer peripheral wall thickness + structural columns |
| 4 | Built-up Area (BUA) | Carpet + Exclusive Balcony/Utility + External Wall Thickness |
| 5 | Common Area Loading | Total common allocation (sq.ft) + Loading % (pro-rata corridors, stairs, lift lobbies, clubhouses, service rooms) |
| 6 | Super Built-up Area (SBA) | BUA + Common Area Allocation |
| 7 | Parking & Ancillaries | Assigned parking (covered/stilt/basement/open), dedicated storage units |

Best practices to embed in the document:
- Print the formula block: **Super Built-up Area = RERA Carpet Area + Balcony/Utility + Walls + Common Loading**
- Unit identification: Unit No., Floor, Block/Tower + boundary directions (N/S/E/W)
- Clear exclusion notes: parking charges, clubhouse membership fees, GST, registration costs, maintenance deposits NOT included in carpet price

## Source data layout (raw sheet, 0-indexed cols)
`# | Unit # | Share(LO/DEV) | Configuration | Floor | Entrance Facing | Toilets | BUA/Plinth | %BUA | Balcony | RERA Carpet | Carpet+Balcony | Common Area | Super BUA | UDS`
- Totals row: Super BUA total (31,853 for Ranka Amber), UDS total = plot area (14,000)
- SSA saleable area (27,543.25 for Ranka Amber) comes from the Supplementary Sharing Agreement / sanctioned plan — NOT derivable from sheet columns. Keep BOTH references in Notes (saleable area SSA basis + Super BUA area-statement basis) so the bank sees no contradiction.

## Computations
- Loading % = (Super BUA − BUA) / BUA × 100 → 16.7%–27.0% for Ranka Amber
- UDS per sq.ft of Super BUA = plot area / total Super BUA (0.4395 for Ranka Amber)

## python-docx pattern (proven)
- Two sections: sec1 portrait A4 letterhead; sec2 landscape (`WD_SECTION.NEW_PAGE`, `WD_ORIENT.LANDSCAPE`, page 29.7×21cm).
- Letterhead: 1×2 table — logo left (DRA logo at `/data/hermes/cache/analysis/dra_logo/dra-logo.png`, width ~4.6cm), company right (navy 1F3864 name "DRA REALTY PVT. LTD.", gold C99A2E tagline "HOME OF PRIDE", grey address/tel/email).
- Navy (sz 18) + gold (sz 8) rules via `w:pBdr` bottom borders.
- Annexure table: 'Table Grid', navy header row (1F3864, white 7.5pt bold), zebra F4F1E8 on even rows, totals row DCE3F0; col widths in Cm.
- Letter signature: Nishant Ranka, Managing Director, DRA Realty Pvt. Ltd.
- Verify after generation by reopening with python-docx: `d.tables[0]` is the letterhead logo table, the annexure table is a later index — check header row, first data row, totals row.

## Pitfalls
- Do NOT present a computed walls column (BUA − Carpet − Balcony) when source figures produce negatives (some Ranka Amber units do) — label the BUA column "[Walls incl.]" and put wall thickness in the notes instead.
- Sheet totals can be off ±2 vs summing unit rows (31,853 vs 31,851) — use the sheet's totals row as authoritative, not the recomputed sum.
- Keep covering letter + annexure notes mutually consistent (saleable area vs super BUA as two explicit references).
- Before regenerating, reuse the prior session's generator script and raw JSON (`/tmp/gen_*.py`, `/tmp/area_statement_raw.json`) — layout is already proven; just restructure the annexure.
