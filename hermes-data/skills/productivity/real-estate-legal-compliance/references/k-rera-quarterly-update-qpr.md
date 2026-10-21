# K-RERA Quarterly Progress Update (QPR) — Filing Recipe

Verified 2026-09-15 on Ranka Amber (DRA Realty). Legal basis: Section 11(1) RERA Act 2016 read with Rule 15(1)(D) Karnataka RERA Rules 2017. Penalties drive compliance — K-RERA circulars (Jan 2026 and each FY) impose ₹25,000/quarter for late/missing QPR, up to 5% of total estimated project cost in serious cases. The portal publishes QPRs publicly — discrepancies are visible to buyers.

## Filing windows (FY cycle, within 15 days of quarter end)
- Q1 (Apr–Jun) → by 15 Jul
- Q2 (Jul–Sep) → by 15 Oct
- Q3 (Oct–Dec) → by 15 Jan
- Q4 (Jan–Mar) → by 15 Apr

First live quarter for a project = the first full quarter after registration date (Ranka Amber registered 05-Aug-2026 → first QPR = Q2 FY26-27, due 15-Oct-2026).

## Correct forms — QUARTERLY UPDATE (NOT registration, NOT completion)
From `rera.karnataka.gov.in/downloadPage`, section "Certificates Required for Quarterly updates (QU) and Annual Reports":
- **Form-4** — Chartered Accountant Certificate (QU) — funds utilisation + 70% escrow reconciliation (8 pages)
- **Form-5** — Architect Certificate (QU) — % work completion (Tables A/B/C)
- **Form-6** — Engineer Certificate (QU) — cost incurred (Tables A/B + Annexure A)
- **Form-7** — Annual Audit Report on Statement of Accounts (annual, separate)

Do NOT use: Form 1/2/3 (registration), completion_Form4/5/6 (project completion), Form-Ex1..Ex7 (extension), modification_form4/5/6. K-RERA rejects the wrong form type.

## Portal access recipe (VPS datacenter IP blocked — tunnel only)
1. Index: `POST /projectViewDetails` with `application/x-www-form-urlencoded`: `district=Bengaluru+Urban&regNo2=<RERA>&btn1=Search` (tunnel `socks5h://hermes-utilities:1000`). The 30MB+ response contains the row; capture `<a id="<detail_id>">` near the project name.
2. Detail: `POST /projectDetails` with `action=<detail_id>` (urlencoded, NOT JSON), headers `Content-Type: application/x-www-form-urlencoded`, `Referer: https://rera.karnataka.gov.in/viewAllProjects`, `X-Requested-With: XMLHttpRequest`.
3. Detail page tab **"Quarterly Updates"** lists exactly what the QPR must cover: extent of work carried out/pending (%), total amount collected/spent/balance, Project Photograph, Current Project Details (Architect cert work-to-date, Engineer cert work-to-date, CA cert funds utilisation), Proposed Project Details (architect/engineer/CA projected, Affidavit, latest EC, 2/3 allottee consent, compensation), Details of Sold/Un-sold units, List of Allottees, NOC Details.

## Quarterly document set (compile each quarter)
1. Form-5 Architect (QU) — signed, site inspection date, % per activity
2. Form-6 Engineer (QU) — signed, cost incurred + balance + Annexure A
3. Form-4 CA (QU) — signed, UDIN, bank reconciliation, receivables + unsold valuation Annexure A
4. Latest Encumbrance Certificate (current quarter)
5. RERA bank statements for the quarter (100%/70%/30% accounts)
6. List of Allottees + Details of Sold/Un-sold units
7. Current-quarter site photographs with GPS
8. Affidavit (no-change / non-litigation as applicable)
9. Supporting baseline: registration cert, sanction plan + building licence, CC status, JDA, eKhata, legal opinion, cost abstract

## House-style drafting rules (user-corrected 2026-09-15 — Prakash Singh)
- **Address the certificate TO THE PROMOTER** — `To, / The M/s <PROMOTER>, / <registered office>` — NOT to RERA officials. Header = bracketed authority line only: `[KARNATAKA REAL ESTATE REGULATORY AUTHORITY (Real Estate (Regulation & Development) Rules, 2017)]`. Do NOT reproduce the K-RERA office letterhead block ("Real Estate Regulatory Authority, Karnataka, #1/14… Mission Road, Bengaluru 560027") — an early draft did this and was rejected as "addressed to RERA officials".
  ⚠️ **Scope caveat (2026-10-05)** — this rule forbids the letterhead when *we* draft the
  certificate's own content. It does NOT forbid it when NDR asks for a **page-exact replica
  of the official QU template PDF** ("make it look exactly the same, including taking images
  from the PDF") — the official Form-5/6/4 carry that letterhead and the replica must too.
  That instruction was given on 2026-10-05 and the letterhead question was raised back to NDR
  as an open item. See `krera-qu-forms-html-replica.md`.
- Field labels in the promoter's filed Form-2/3 style: `RERA No : …` / `Project Name : …` / `Promoter Name : …`, projector named `M/s <PROMOTER>`.
- Reuse the promoter's already-filed plot description verbatim (Village / Taluk / District / PIN / boundaries / land area), add the lat-long end-point coordinates (QU forms require them).
- Signature blocks mirror filed forms: Name, License No, Address, Contact No, Email, Website, Place, Date + the standard "*The same Engineer/Architect is responsible… approval needs to be taken from the Authority" note.
- **Fidelity rule:** when the user supplies the official RERA PDFs ("can you confirm whether you have taken this form… if not prepare using these"), md5-compare your source vs their upload, re-OCR at 150–200 dpi, and rebuild page-strict. Do NOT compress official tables into single lines. My first Form-4 draft compressed Borrowings/Mortgage, Additional Information 1–5 and Annexure A into prose — rebuilt as full tables.

## Build pattern that worked
- Split the HTML build into small modules: `qpr_common.py` (shared header/plot fragment), `qpr_form5.py`, `qpr_form6.py`, `qpr_form4a.py` + `qpr_form4b.py` (Form-4 is 8 pages — split to keep each file small), then a `qpr_build.py` runner that imports them, creates Google Docs via `MediaIoBaseUpload(html, mimetype='text/html')` (never text/markdown — silently creates empty docs), trashes superseded drafts, updates the master checklist sheet rows, sets anyone-reader.
- Verify by reading the doc back with the Docs API recursive walker (text lives in `textRun.content` and inside table cells — a naive top-level join returns 0 chars and falsely signals failure).
- File the templates under `RANKA Amber - Scanned Documents for RERA Approval` (psingh-owned, writable); wire links into the QPR document-set sheet (old row IDs go stale — update after rebuild).

## Ranka Amber ground truth (worked values, Sep 2026)
- RERA: PRM/KA/RERA/1251/446/PR/050826/008859 (detail id 14833; index shows ACK/KA/RERA/1251/446/PR/030726/010383). Registered 05-08-2026, end 31-07-2029, status "New Project Launch", No complaints.
- Project: 1 block (Block A), Stilt+Ground+3, 20 units 3 BHK, carpet 2,165 sqm, 22 covered parking, land 1,301 sqm (A1 705 + A2 596), FAR 1.97, height 14.99 m.
- Costs: Land ₹7,50,00,000 + Development ₹6,63,81,676 = Total ₹14,13,81,676. Engineer cost abstract ₹5,69,75,601.
- Bank (Kotak Mahindra, IFSC KKBK0000431, 100 Feet Road HAL 2nd Stage Indiranagar): 100% collection 8551119387, 70% designated 8551119394, 30% operative 8551119370.
- Professionals: Architect Anjali Mandhyan CA/2018/100260 (findingform); Engineer Loganathan M SLVS BCCL/BL-3.6/E-0293/24-25; Structural Manoj Kumar Reddy.
- Approvals: sanction GBA/BECC/0540/25-26 + LP GBA/MDP/DDTP/0007/26-27 + licence BBMP/CC/4247/26-27 (18-05-2026); CC application Annexure VIII/IX in progress (tracker P-098); BESCOM temp power 15-Jun-2026.