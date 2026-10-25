# MOA/AOA Constitutional-Capacity Review — "does the entity's constitutional docs permit X?" (verified 2026-09-16)

Answering the diligence checklist item: *The Constitutional Documents (MOA/AOA)
of the entity must permit entering into partnerships and investing immovable
property as capital.* Worked example: DRA Realty Private Limited — and the
general procedure.

## General procedure

1. **Locate the docs on Drive**: search `name contains 'Memorandum'`,
   `'Article of Association'`, `'incorporation certificate'`, `'MOA'`. Copies
   repeat in several folders — byte-download and COMPARE sizes to confirm the
   same document (all copies were byte-identical in the DRA Realty case).
2. **Read the full objects clause**, not just the visible page: MOA is short
   (4 pp — read ALL pages). AOA is long (22 pp) — grep per-page OCR for the
   keywords that matter to the specific ask (`partner`, `venture`, `immovable`,
   `invest`, `acquire`, `purchase`, `capital`).
3. **Scans with a garbled embedded text layer**: `pdftotext -layout` can return
   interleaved column garbage (multi-column OCR overlay). Reliable route:
   `pdftoppm -r 200 -png` per page + `tesseract <pg>.png stdout --psm 3`
   (default psm may return EMPTY — always retry `--psm 3`).
4. **Classify the finding** into express / incidental-only / absent:
   - partnership power = express clause like "to enter into partnership or into
     any arrangement for sharing of profits / joint venture" — ABSENT here;
   - holding & dealing in immovable property = express (real-estate objects);
   - contributing immovable property AS CAPITAL to a partnership = a *partnership
     act* → absent when the partnership power is absent (ultra vires exposure).
5. **Report verdict per requirement** (✅/⚠️/❌), cite clause numbers, then the
   fix: Special Resolution to alter the MOA objects + file Form MGT-14 with ROC
   within 30 days.

## DRA Realty Pvt Ltd worked facts

- CIN U70100KA2011PTC058105. Incorporated 07-04-2011 as **Southcity Retail Plus
  Private Limited**; renamed **DRA Realty Private Limited** w.e.f. **08-Dec-2020**
  (CoI pursuant to change of name, RoC Bangalore). Main objects 2–4 inserted +
  revised AOA adopted by Special Resolution at EGM **16-Nov-2020**.
- **MOA (4 pp) — objects:**
  - (A) Main: (1) retail trade; (2) developers of urban/rural immovable property —
    act as builders, real estate developers, acquire/purchase/lease/exchange land,
    estates, buildings, develop/redevelop, create residential/commercial/
    industrial buildings, townships etc.; (3) purchase/acquire land, build
    townships/markets, advance money to and enter contracts/arrangements with
    builders/tenants; (4) software business.
  - (B) Incidental/ancillary: (1) agreements/contracts for technical/financial
    assistance; (2) advertising; (3) patents/trademarks/licenses; (4) arrangements
    with Govt/State authorities.
  - **NO partnership / JV / profit-sharing clause anywhere in the MOA.**
- **AOA (22 pp, Companies Act 2013 + Table F applies):**
  - cl.81 collaboration arrangement (Indian/foreign enterprise, company,
    corporation, firm or person — supply of technical know-how/machinery;
    collaboration director; equity shares for non-cash consideration);
  - cl.82 foreign nationals/NRIs may invest in share capital; allotment for
    non-cash consideration pursuant to "collaboration or joint venture business
    with the Company in India" — NARROW (share-allotment context, not a general
    partnership power);
  - cl.103 reserves may be invested in investments other than shares of the
    company (surplus-funds investment, not property-as-capital);
  - cl.70/98/99 borrowing, mortgage, charge powers.
- **Verdict:** can acquire/hold/develop/sell immovable property ✅; can enter
  partnerships or contribute immovable property as partnership capital ❌ (not
  expressed → ultra vires). Investor docs (DRA KAAJ-style contribution schedule)
  need the MOA amended first.

## Drive file IDs (re-verify, folders move)

- `Firm - DRA Realty Private Limited` folder 1m8tyLI60KhMkNdB8TziCWQpDDNDKijuq:
  MOA `Memorandum of Association (2).pdf` 1Z-TyqKY0RkUWnv78mL3WEReyrc3Yl_bl;
  AOA `Article of Association.pdf` 1QdFc8Y0llojmkI04G_zTA4W5Ko0I7MXW;
  CoI 173agTIxhI0o4xJEK1bnTsq5g5o6uU6Y1.
- `DRA Realty Pvt Ltd - firm related documents` folder 1ovD6huqRiJgw4-IUflKjmDY0GEKDniCl
  (copies: MOA 1JezbvzIqRO18SF6Oy6AZJELVHw1POvLO, AOA 1dtcQbpspj5j3IhWqCmhUM5Hgb6S3t5JD).
- Related: 2026-06-24 Board Resolution DRA Realty → DRA KAAJ Dev Partners
  (1MJou2IKKDdOe2NCrlpoVcJ_SFvCll3Fu) — the contribution class this checklist
  feeds; BR text confirms Managing Partner role, 51:49, Palya/Byadarahalli/
  C.R. Nagendra lands, ₹10 Cr capital.

## Pitfalls

- Certified-true-copy stamps say **SOUTHCITY RETAIL PLUS PRIVATE LIMITED** on a
  document titled DRA REALTY — that is expected (pre-rename certification), NOT
  a wrong-file signal.
- pdftotext on these scans interleaves pages into garbled word salad — never
  quote MOA/AOA text from `pdftotext -layout` alone; verify with per-page
  `--psm 3` tesseract.
- AOA page 22/22 can be signature-only; the objects/collaboration clauses are
  in the middle (pp 14–19 for directors' powers, borrowing, dividends).
- Table F applies by default (AOA cl.1) — check Table F in Schedule I if hunting
  for a power not expressly modified by the AOA articles.