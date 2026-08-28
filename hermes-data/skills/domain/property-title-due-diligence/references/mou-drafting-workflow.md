# MOU Drafting Workflow (DRA Land Acquisitions)

Class of work: drafting Memoranda of Understanding for DRA's land
acquisitions (Bestamanahalli, Doddamarali-LG Lands, future deals).
Deliverable = a native Google Doc owned by psingh@draas.com, link sent
in a code block.

## Inputs (typical)
1. Google Sheet — RTC summary / survey list (Sl No, Survey No, Village,
   Landowner, Extent A:G, Kharab A/B, Total, Khata No, transaction details).
2. Proposal PDF — often STALE. Treat user's stated terms as authoritative
   and flag every discrepancy (price, acreage, phase split). Example:
   Doddamarali proposal said ₹2.80 Cr/ac, 80A, 25/25/30 phases; user
   terms were ₹4 Cr/ac, ~70A, 10A + 20A lots.
3. Template MOU — reuse the Bestamanahalli MOU v3 structure verbatim.

## Template-read pitfall (IMPORTANT)
BM MOU v3 (`13n53Ouoq2miq1FGwfFHROwj_GqcJLcUdYxluMAE_eLs`) was historically
table-layout; as of Aug 2026 it is paragraph-structured — `docs.documents().get()`
returns real paragraphs with extractable text (walk body content recursively incl.
tables to find clause startIndices). If a doc still reads empty via docs.get(),
fall back to Drive export:
  drive.files().export(fileId=..., mimeType='text/plain')
Drive export is the ground truth for verification regardless.

## Build (python-docx)
- Env: /tmp/docxvenv (uv venv + pip install python-docx). Recreate if missing.
- Helper functions: para() / title() / part_heading() / clause(). clause()
  must accept align= and italic= kwargs or the build dies mid-way.
- Annexure survey tables: style='Table Grid', fonts 8.5–9pt (wide 8-col
  tables), header row bold. Keep summary rows (SUBTOTAL/GRAND TOTAL) from
  the sheet, bold.
- Blank placeholder tables for survey allocations not yet fixed
  (Phase 1 / Phase 2+ / JDA lands).

## Deal-type variants
- Multi-party outright purchase (Bestamanahalli): FP1–4 each with own
  Annexure (1–4) survey list; purchaser-protective (binding intent,
  no-dealing lock, advance + 12%/18% interest, NO specific performance).
- Aggregator MOU (Doddamarali-LG): single FIRST PARTY = land aggregator
  who procures/coordinates landowner sales; key clause 5.1(e) — First
  Party must organize DIRECT MEETINGS with landowners and obtain written
  consent from ALL family members / legal heirs (condition precedent);
  JDA carve-out (~7A) via Joint Development Agreement for plotted
  development, terms in Definitive Documents (Clause 4.4 + Annexure D).
  Per-acre price is pre-conditioned on Phase 1 completing within 60 days.

## Aggregator-MOU clause additions (user-approved, Aug 2026)
- **4.10 Physical Measurements / Joint Survey** (inserted after 4.9, Part IV):
  extent verified by physical measurements and/or joint survey (incl. compound /
  actual boundaries) at FIRST PARTY's cost; if discrepancy between survey-record
  extent and measured extent → sale consideration paid on ACTUAL physical
  measurement / joint-survey extent, AND/OR survey records updated with revenue
  authorities (new survey number or **11E proceedings under the Karnataka Survey
  and Boundaries Act, 1961**) BEFORE payment for that land; SECOND PARTY's reps /
  surveyors may be present. Rationale: per-acre price makes extent the unit of
  payment, so the clause fixes what happens when recorded extents don't match
  the ground.
- **7.4 Notification of Acquisitions** (inserted after 7.3, before Force Majeure;
  renumber old 7.4 → 7.5): FIRST PARTY promptly notifies SECOND PARTY in writing
  of (a) any acquisition/proposed acquisition of ADDITIONAL lands intended to be
  aggregated into the Schedule Properties (with full particulars), and (b) any
  acquisition proceedings / notifications by any authority under any land
  acquisition law (incl. RFCTLARR 2013) affecting the Schedule Properties;
  added lands form part of the deal ONLY on SECOND PARTY's prior written consent.

## Standard clause — 7.2 Notice of Registration / Execution (user-approved, Aug 2026)
User dictates this clause verbatim for both aggregator and multi-party MOUs. Approved wording (Doddamarali-LG 2026-08-07, Bestamanahalli v3 2026-08-07):
- First Party communicates the execution/registration schedule in writing **at least 15 (fifteen) days prior** for each phase, subject to **Second Party's legal advisors' clearance**
- Any claims/issues from landowners on title, third-party claims, existing **judicial/ongoing proceedings** → **sorted and cleared by First Party at his own cost**
- Execution proceeds **only after all cleared + written confirmation** by First Party
Deal-variant adaptation: single aggregator → "FIRST PARTY / his own cost"; multi-party (4 FPs) → "FIRST PARTIES / their own cost" (matches doc's plural usage).
Insert at Part VII start (before old 7.2 prompt-disclosure clause), renumber 7.2→7.3→7.4→7.5, render inserted text BLUE (redline convention). Use equal-length delete+insert for renumbering (zero index shift).

## User-delegated clause drafting ("complete this clause as needed... where it deems fit")
Prakash often gives a rough clause intent and delegates completion + placement (Doddamarali-LG 2026-08-07: physical-measurement clause, notification-of-acquisitions clause). Pattern:
- **Complete** the clause with standard protective drafting (who bears cost, what happens on discrepancy, deadlines, consent rights) — don't ask where to put it.
- **Placement logic**: payment/consideration/measurement clauses → Part IV (Consideration and Payments); notice/notification duties → Part VII (after the prompt-disclosure clause); title/diligence/survey clauses → Part III. Number as the next free clause in that Part (4.10, 7.4...), renumber later clauses with equal-length delete+insert.
- Flag assumptions back to user in the delivery note (e.g. "I added 'at the cost of the FIRST PARTY' — say the word to change") so he can veto cheaply.
- Land measurement clause pattern (aggregator MOU): joint survey/physical measurement at FP's cost; discrepancy between recorded and measured extent → price paid on physical measurement OR records updated (new survey number / 11E proceedings under Karnataka Survey & Boundaries Act 1961) before payment; SP present at measurement.

## Standard clause — 4.10 Physical Measurements / Joint Survey (drafted 2026-08-07, user-requested for Doddamarali-LG)
User's raw ask: "physical measurements or joint survey, if any discrepancy in each survey nos then the price will be paid on the physical measurements or to be updated in the new Survey no or 11E". Drafted as new Clause 4.10 at end of Part IV (Consideration & Payments, after 4.9) — the payment-relevant home, NOT Part III due diligence. Core elements:
- Extent verified by physical measurements and/or joint survey of the lands (incl. compound / actual boundaries), joint, at FIRST PARTY's cost
- If discrepancy between recorded extent (revenue/RTC/survey records) and physical measurement → price paid on actual physical measurements / joint survey extent
- AND/OR survey records updated with revenue/survey authorities — new survey number OR 11E proceedings (Karnataka Survey and Boundaries Act, 1961) — BEFORE consideration paid
- SECOND PARTY may have representatives/surveyors present during measurements
Note: 11E = Karnataka Survey & Boundaries Act 1961 re-survey/boundary determination; don't invent other statutory bases.

## Standard clause — 7.4 Notification of Acquisitions (drafted 2026-08-07, user-requested for Doddamarali-LG)
User's raw ask: "IF ANY acquisitions etc to be notified to the Second party". Drafted as new Clause 7.4 in Part VII (Timeline), inserted BEFORE Force Majeure (renumber old 7.4→7.5). Core elements:
- FIRST PARTY promptly notifies SECOND PARTY in writing of: (a) any acquisition / proposed acquisition of additional lands to be aggregated into Schedule Properties (with full particulars); (b) any acquisition proceedings / preliminary or final notifications by any authority under any land-acquisition law (incl. RFCTLARR 2013) affecting the Schedule Properties
- Lands so acquired form part of Schedule Properties ONLY upon SECOND PARTY's prior written consent
Placement logic: notification duties cluster in Part VII (next to 7.2 registration notice, 7.3 prompt-inform). Do NOT put in Part VI representations — that's warranty territory, this is an ongoing covenant.

## Upload & verify
- Upload: drive.files().create with
  mimeType='application/vnd.google-apps.document' (converts DOCX), then
  permissions().create to psingh@draas.com (role writer → becomes owner).
- Verify: re-export the uploaded doc to text/plain, grep key clauses +
  price + acreage + annexure headers, and assert annexure table row
  counts (49 data rows + header + subtotals = 53).
- Filename convention: YYYYMMDD MOU_<Deal> (e.g. 20260807 MOU_Doddamarali_LG_Lands).

## Deliver
- Google Docs link inside a code block (Telegram breaks plain URLs);
  fallback: "search Drive by filename".
- Flag: (1) discrepancies between sheet phase labels and user's phase
  terms, (2) stale proposal figures superseded, (3) blanks left for
  user/other party to fill (names, Aadhaar/PAN, CIN, token amount, emails).
