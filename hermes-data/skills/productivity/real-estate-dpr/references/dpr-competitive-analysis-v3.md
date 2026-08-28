# DPR Competitive Analysis Pass (v3 runner, 24-Aug-2026)

Session record for "ADD: COMPETITIVE ANALYSIS IN ALL THE DPR'S" — the bug found,
the fix pattern, and the per-project named-competitor tables.

## The bug this pass uncovered

All 4 Ranka DPRs shipped with Section 5.2 rendering the placeholder
`Competitor benchmark table — from per-project R&D decks` **even though real
competitor data existed** — in `run_dpr_docx.py`, the OLD v1 runner that imports
`build_dpr_docx` (the v1 builder). The v2 builder (`build_dpr_docx_v2.py`,
images/entity/coords pass) only carried `plan_img / floor_imgs / render_img /
site_imgs / rera_img / loc_map / annex_imgs / entity_partners / coords` keys.
`market`, `comp_rows`, `positioning`, `annex_links` were all None → 5.1 stage
placeholder + 5.2 placeholder + Section 10 live links missing.

Root cause: **per-pass data overrides lived in a runner outside the builder, and
the runner was never re-pointed at the new builder.** When the builder is
rewritten, runner-level data silently vanishes unless deliberately ported.

Detection: reopen each .docx with python-docx, find tables with 4-column first
row, assert first cell == 'Competitor / Bench'. A placeholder paragraph, not a
table, is a failed ship.

## Fix pattern (import-safe builder + single runner)

1. Remove the auto-run loop at the bottom of the builder module
   (`for name in [...]: build_dpr(P[name])`) — a builder that builds on import
   can neither be imported for reuse nor patched incrementally.
2. Runner imports the builder, applies ALL per-project overrides for the current
   pass on top of `P` (market, comp_rows, positioning, annex_links), THEN calls
   `build_dpr(P[key])` per project.
3. Keep every per-pass data override in the runner alongside the build calls so
   no future pass drops data the previous pass had.

## Competitor table structure (matches user's "COMPETITIVE ANALYSIS" ask)

- Columns: `['Competitor / Bench', 'Type', 'Price (₹/sq.ft)', 'Notes']`
- Rows: market-wide band row(s) + 6–16 named competitors with real researched
  ₹/sqft + the project's own row (`Ranka X (own)`) with price (achieved vs
  assumed, flagged).
- A bold `Positioning:` paragraph after the table: own price vs band, headroom
  rationale, cite sales evidence where possible.
- Data source: `property-pricing-sources` → `references/ranka-project-pricing-rnd-index.md`
  — NO fresh web research needed for Ranka projects (Tavily often 432).
  Figures are asking/listed rates (Aug-2026), not transaction data — say so in
  the doc.

## Per-project named competitor sets (Ranka pricing R&D index, Aug-2026)

- **Amber (Whitefield 2–3 BHK)**: band 8,000–17,000; premium new stock
  14,000–29,000; Sumadhura Folium ~28,700; Prestige Raintree Park ~27,500;
  Jagriti Renaissance ~12,500; Sraddha Splendor ~8,300; Vishnu Residency ~7,900;
  own ₹12,000 achieved (4 units sold).
- **Udaya (Hosur corridor plotted)**: corridor 2,785–9,500; Hosur town
  3,000–5,500; Bagalur airport zone 1,500–3,500; Concorde Mist Valley ~2,785;
  NBR Trifecta ~3,349; Aspire Boulevard ~4,000; Ecocity 5,375–5,400; Palm
  Paradise ~5,500; Confident Gardenia 5,500–7,000; Azalea 5,875–6,000; Saikam
  Aananda 6,333–7,408; Morefields 8,000–9,500; own ₹3,200 sold / ₹3,500 unsold
  (model assumes 4,000).
- **Oasis (Sarjapur–Hosur villa corridor)**: entry 6,700–9,600, ongoing
  8,500–11,000, ready premium 10,600–12,300; Pelican Square 7,400–7,900; Shriram
  Chirping Grove 6,700–9,100; Arvind Forest Trails 8,500–9,000; Kumari Oakville
  9,500–10,000; Mitta Orrin 10,100–11,000; Ruchira Villa Feliz ~11,000; NVT
  Arcot Vaksana 10,600–12,300; Assetz 18&Oak 10,900–12,000; own ₹12,000 assumed
  BUA (DTCP 7.53 ac + RERA obtained).
- **NorthStar (Yelahanka)**: band 6,500–23,000; luxury 14,000–23,000 (Brigade
  Eternia 14–16K, VISISTA 15–17K, Concorde Mayfair ~14.5K avg, Godrej Aveline
  16.2K avg up to 18.1K, L&T Elara Celestia 18–23K); premium/mid 6,500–12,200
  (GR OPAL ~6.5K, MLN Signature ~6.75K, Sumuk Square 7.1–7.5K, Jahnavi Brindavan
  7.75–8K, Casagrand Promenade 7.5–7.9K, Sobha Althea 8.1–14.2K, Aryan 1 Celeste
  9.5–10.3K, Fortuna Acacia 10–11.5K, TrendSquares Ortus III ~11.5K, Flowing
  Tree ~12.2K); own ₹12,000 assumed pre-launch.

## Stable-link upload on regeneration

Regenerating .docx after a data patch:

- Upload with `drive.files().update(fileId=<existing id>, media_body=MediaFileUpload(path, mimetype=DOCX_MIME), fields='id,name,size,modifiedTime')`
  — **preserves the file IDs/links already delivered to the user** (folder link
  + per-file links stay valid). Delete+create changes IDs and breaks every link
  sitting in chat history.
- Re-assert `anyone -> writer` permission after the update.
- Verified 24-Aug-2026: 4/4 updated in place (sizes changed, modifiedTime newer,
  folder listing showed same IDs).