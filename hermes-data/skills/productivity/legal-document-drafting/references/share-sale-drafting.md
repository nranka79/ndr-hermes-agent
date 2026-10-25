# Share Sale / Share Purchase Agreement Drafting (Indian private company)

Class-level playbook for drafting a share transfer package in a closely-held
Indian private company — DRAAS context: land-holding SPVs, distressed sellers,
a single buyer taking control (e.g. 98% via 490+490 of 1000 shares).

## Triggers
"share purchase agreement", "SPA", "sell shares", "transfer of shares",
"board resolution for share sale", "share certificate / folio" requests.

## Document set (deliver in this order)
1. Board Resolution (minutes) — consent to transfer, approval of the SPA,
   cancellation of old certificates / issue of new ones, register of members
   update, authorization to sign + make statutory filings.
2. Members' written consent — CRITICAL when the sellers ARE the entire board:
   both directors, as shareholders, consent in writing and waive any
   pre-emption / ROFR under the AoA. A board resolution passed by the sellers
   themselves is legally thin on its own; ship the member consents in the same
   package.
3. Share Purchase Agreement — ONE PER SELLER when each seller transfers a
   separate block (e.g. 490 + 490 shares) — matches NDR's "agreements" plural;
   alternatively one consolidated SPA. Each seller's price may differ.
4. SH-4 instrument(s) of transfer — transferor + transferee both sign;
   lodgement with the company within 60 days (Sec 56, Companies Act 2013).
5. New share certificate drafting: cancel old certificate(s), issue new one(s)
   to buyer, re-issue balance to sellers; carry forward folio/point to new
   folio numbers.
6. Register of members (MGT-2) update. Note the Sec 29 demat requirement for
   private companies (except "small companies") — confirm classification
   before assuming physical-share mechanics apply.

## Board resolution drafting notes
- Sec 184 interest disclosure: both directors are interested (they are the
  sellers) — record the disclosure in the minutes.
- Transfer approval itself needs no ROC e-filing; SH-4 is lodged with the
  company and the transfer is reflected in MGT-2. MGT-14 only if the AoA is
  altered. PAS-3 is for allotments, not transfers.

## SPA recital chain (matters for DRAAS land SPVs)
Formation/object → the specific land asset (survey no, extent, village,
purchase deed doc no + date) → litigation summary (case no, court, status,
pending IA) → encumbrances (mortgage to lender: date, doc no, amount,
outstanding) → pending third-party rights (e.g. title release still required)
→ buyer's prior advances/support → board/members' decision to sell → agreement.
Key clauses: definition of Shares; Consideration & payment mechanics
(INCLUDING set-off of buyer's prior advances — ask, don't assume); Conditions
precedent (title release, mortgage settlement, approvals); Representations &
warranties (seller: title to shares, no liens on shares, true disclosure of
litigation/mortgage; buyer: funds); Closing & delivery (certificates, SH-4,
consents); post-closing covenants (board change, control); indemnities;
governing law.

## Pre-drafting checklist — ask the user BEFORE drafting
- Exact registered name + CIN + registered office; get from the company master
  page scan / MCA. Voice name often differs from registered name.
- Buyer exact name as on PAN (voice variants common — confirm against PAN/ID).
- Seller full names, PANs, addresses as on PAN.
- Share certificate details: certificate no(s), folio no(s), distinctive nos,
  face value, total issued capital; confirm NO third-party minority beyond the
  sellers.
- Consideration per share / total; set-off of past advances.
- AoA transfer restrictions / pre-emption (ask for the AoA extract).
- Land deed + mortgage deed + title-release details for the recitals.

## Pitfalls (live session Sep 2026 — Meteoroids Developers Pvt Ltd)
- User dictated "Meteorite Developers"; registered name per court plaint is
  "Meteoroids Developers Pvt Ltd". ALWAYS confirm the registered name from an
  actual document before drafting.
- Buyer dictated "Chaitra Murjani"; records had "Charitra 'Chinks' Murjani".
  Flag and confirm the PAN-version spelling — re-issuing an instrument set
  after signature is costly.
- User said scans were coming; /mnt/uploads actually contained unrelated
  files (Scribd screenshots, another project's khatha PDF, old BBMP forms).
  Verify uploads match the task and REPORT what actually arrived (file list +
  content), then ask for the missing originals. Don't draft from gaps.
- Prior litigation sessions carry the factual backbone (case no, property,
  directors, purchase deed details). Run session_search on the company name
  first — it also yields the registered-name clue.
- Company-aggregator lookups (zaubacorp) are Cloudflare-gated even via the
  r.jina.ai proxy; Bing-via-Jina returns unrelated results for exact Indian
  company names. Get the CIN from the user's master-data scan instead of
  scraping.