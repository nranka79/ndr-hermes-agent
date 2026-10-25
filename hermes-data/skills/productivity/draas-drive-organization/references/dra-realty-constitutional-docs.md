# DRA Realty Pvt Ltd — Constitutional Documents (MOA/AOA) Verification

Use for "check the MOA/AOA of DRA Realty" / "does the entity permit partnerships / investing immovable property as capital" / any object-clause review of a DRA-group company's constitutional docs. Verified 2026-09-16 from psingh@draas.com token.

## Where the docs live

- **`Firm - DRA Realty Private Limited`** folder `1m8tyLI60KhMkNdB8TziCWQpDDNDKijuq` (parent `1Y2UFlSieN16TFdlQgb9tsQOUBMTCnNGr`) — canonical set:
  - MOA: `Memorandum of Association (2).pdf` `1Z-TyqKY0RkUWnv78mL3WEReyrc3Yl_bl` (4 pp, 1,371,733 B)
  - AOA: `Article of Association.pdf` `1QdFc8Y0llojmkI04G_zTA4W5Ko0I7MXW` (22 pp, 8,645,836 B)
  - CoI: `DRA Realty incorporation certificate.pdf` `173agTIxhI0o4xJEK1bnTsq5g5o6uU6Y1`
  - Also holds: Board Resolution for Authorized Signatory (05-04-2025), e-PAN, GST cert, director KYC/ITR files
- **`DRA Realty Pvt Ltd - firm related documents`** folder `1ovD6huqRiJgw4-IUflKjmDY0GEKDniCl` (under `1sG1KlY-higI7vhoafHmyarS_qIWkspEW`) — "Copy of" MOA/AOA/CoI; byte-identical sizes to canonical (verify by size, don't re-OCR every copy).
- Additional byte-identical copies under **Ranka Udaya** (`1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z`): MOA `10JWGyG20tcUXJ61Oyv9YwYfm8-arbaaR`, AOA `1_S7MbVBTDMOVZyEddBeXMmosnODwaGH5`.
- Other entities follow the same naming pattern: e.g. Thindlu constitutional docs under `Firm Related Documents` `1u7tPOk_hrafr0bYXSh0XAeSlg290l1Bw`. Search recipe: `name contains 'Memorandum'`, `name contains 'Article'` (AOA rarely matches a name query), `name contains 'Firm'`, then walk parents to the "Firm - <entity>" folder.

## Entity facts

- Incorporated 2011 as **SOUTHCITY RETAIL PLUS PRIVATE LIMITED**; CIN `U70100KA2011PTC05...`; renamed **DRA Realty Private Limited** w.e.f. **08-Dec-2020** ("Certificate of Incorporation pursuant to change of name").
- MOA main objects 2–4 inserted and AOA revised per **Special Resolution passed at EGM 16-Nov-2020** (note appears on MOA p.2 and AOA p.1). AOA header: "The Companies Act, 2013 / Company Limited by Shares", Table 'F' applies (cl. 1).
- Registered address per CoI: 201A/202BA Queens Corner, No.3 Queens Road, Bangalore 560001.
- The certified-true-copy stamp says "For SOUTHCITY RETAIL PLUS PRIVATE LIMITED" because the certified copy predates the rename — expected, not a mismatch.

## MOA object summary (page-level tesseract OCR)

Main objects (A):
1. Retail trade — malls, hypermarkets, warehouses, distribution, showrooms.
2. **Developers of urban and rural immovable properties** — builders, real estate developers, acquire/purchase/lease/exchange/deal in land, estates, buildings; develop/redevelop residential/commercial/industrial.
3. Purchase/acquire/lease/exchange land in any lawful manner, turn to account, develop, dispose of; build townships/markets; **advance money to and enter contracts/arrangements with builders, tenants and others**.
4. Software / IT business.

Incidental objects (B): (1) agreements with Indian/foreign individuals/companies for technical/financial/other assistance; (2) advertising; (3) patents/trademarks/licenses; (4) arrangements with Govt/State Authorities.

**KEY FINDING — NO partnership / joint-venture / profit-sharing clause** anywhere in MOA or AOA. Only narrow mentions: AOA cl. 82 (foreign nationals/NRIs subscribe shares for non-cash consideration under a collaboration/joint-venture arrangement) and AOA cl. 81 (collaboration director + non-cash allotment for know-how/machinery). AOA cl. 103 (Board may invest reserves in investments other than company shares) covers surplus funds only.

## Verification verdict template

- "Entity may **enter into partnerships**": ❌ not expressly permitted → the act would be ultra vires the objects (relevant where DRA Realty is/would be a partner — e.g. DRA KAAJ Devp Partners, Reconstitution Deed contexts).
- "Entity may **invest immovable property as capital**": ⚠️ owning/dealing in land is clearly covered (obj. 2 & 3), but contributing land **as partnership capital** is itself a partnership act → not covered without an express clause.
- Remedy: Special Resolution to insert an express objects clause + Form MGT-14 filed with ROC within 30 days.

## Standard amendment clause (partnership + property-as-capital)

> "To enter into partnership or into any arrangement for sharing of profits, union of interests, co-operation, joint venture, reciprocal concession or otherwise with any person, firm or company carrying on any business which the Company is authorised to carry on, and to contribute, transfer or apply any properties, assets or funds of the Company (including immovable property) to any such partnership or joint venture as capital or otherwise."

## Pitfalls

- **Garbled OCR text layer on scanned MOA/AOA (2026-09-16).** `pdftotext -layout` on these scans SUCCEEDS but returns interleaved multi-column word-salad (half-words, fragments from other clauses on the same line). It greps "fine" for keywords and cannot be quoted verbatim. Always verify at page level: `pdftoppm -r 200 -png <pdf> pg` then `tesseract pg-N.png stdout` per page; cross-check clause numbering continuity (e.g. AOA cl. 80→81→82, 98→99→100) before quoting any finding.
- vision_analyze may 503 ("no LLM keys configured") — tesseract is the standing fallback for these scans (see SKILL.md pitfall).
- Object findings must be anchored to clause numbers + the EGM amendment note (16-Nov-2020) so the reviewer can distinguish original vs inserted objects.