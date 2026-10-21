# K-RERA Quarterly Update (QPR) Filing — Document Set & Form Formats

Verified 2026-09-15 on **Ranka Amber** (DRA Realty Pvt Ltd).

## Legal basis, deadlines, penalty

- **S.11(1) RERA Act 2016** read with **Rule 15(1)(D) Karnataka RERA Rules 2017**.
- Filed on the K-RERA portal by the **promoter's registered login** (not a
  paper submission).
- **Deadlines — within 15 days of quarter end:** Q1 → 15 Jul, Q2 → 15 Oct,
  Q3 → 15 Jan, Q4 → 15 Apr. (Some secondary sources say 30 days; the K-RERA
  circulars and the penalty mechanics use 15 days. Go with 15.)
- **Penalty:** ₹25,000 per quarter, auto-levied on delay/non-submission;
  up to **5% of total estimated project cost** in serious cases
  (S.38(1) r/w S.61).
- **QPRs are published publicly** on the portal — buyers and competitors read
  them, so reported percentages must match the certificates.
- **First applicable quarter** = first full quarter-end after registration.
  Ranka Amber registered 05-08-2026 → first QPR is Q2 FY 2026-27 (quarter ended
  30-09-2026), due 15-10-2026.

## What a quarterly update contains

Taken from the **"Quarterly Updates" tab on the portal's project detail page**
— that tab is the authoritative field list; scrape it rather than guessing.

*Current Project Details:*
- Extent of work carried out till date (%) / extent pending (%)
- Total amount collected / spent for the project / balance lying with promoter
- Architect Certificate — Work Completion Schedule till Date
- Engineer Certificate — Work Completion Schedule till Date
- CA Certificate — Funds Utilization

*Proposed Project Details:*
- Architect Cert — pending work completion schedule
- Engineer Cert — pending work completion schedule
- CA Cert — funds required for project completion
- Affidavit; Latest Encumbrance Certificate
- Whether 2/3rd consent of allottees taken; whether compensation provided

*Other:* Details of Sold/Un-sold Units · List of Allottees · List of Complaints /
pending litigations · **Project Photograph with GPS** · NOC details + validity &
renewals · Project Extension details (if any).

## The three QU certificates — form numbers matter

| Form | Who signs | Purpose |
|---|---|---|
| **Form-4** | Chartered Accountant | Funds utilisation, 70% escrow, bank reconciliation, receivables/unsold valuation (Annexure A) |
| **Form-5** | Architect | Percentage of completion — Table A (building-wise activities), Table B (internal/external development works), Table C (other amenities) |
| **Form-6** | Engineer | Cost incurred vs estimated — Table A (building), Table B (entire phase development works) |
| Form-7 | CA | Annual Audit Report on Statement of Accounts (annual, S.4(2)(l)(D)) |

> **Pitfall:** the registration set is Form-1 CA / Form-2 Architect /
> Form-3 Engineer. Reusing those scans in a QPR gets rejected for an ongoing
> project. Also distinct again: Form-4/5/6 *for project completion* and
> Form-Ex1…Ex7 *for extension* are different documents.

## Download URLs (official)

Base: `https://rera.karnataka.gov.in/resources/downloads/`

- Form-4 CA (QU): `Form-4.pdf`
- Form-5 Architect (QU): `From-5%20Architect%20Certificate%20(QU).pdf`
  ← **the official filename is misspelled "From-5", not "Form-5"** — a
  `Form-5...` URL 404s. This trips a naive fetch every time.
- Form-6 Engineer (QU): `Form-6%20Engineer%20Certificate%20(QU).pdf`
- Form-7 Annual Audit: `Form-7.pdf`

Same page, other sets:
- Completion: `completion_Form4.pdf`, `completion_Form5.pdf`,
  `completion_Form6_Plots.pdf`, `completion_Form6_Projects.pdf`
- Extension: `Form-Ex1`…`Form-Ex7` (Ex1 architect status of work as on date,
  Ex2 architect pending work, Ex3 CA fund utilisation, Ex4 CA fund required,
  Ex5 engineer status of work, Ex6 engineer pending work, Ex7 affidavit for
  extension), plus `FORM-B`
- Modification: `/resources/staticpage/modification_form4.pdf` (and `form5`, `form6`)
- Post-registration: Form-1/2/3 (PR) under `/resources/downloads/`

**All these forms are scanned image PDFs with NO text layer** — `pdftotext`
returns empty. Extract with `pdftoppm -r 150 -gray -png` + `tesseract`.

**Network:** K-RERA blocks the VPS datacenter IP. All requests must go through
the residential SOCKS proxy: `curl --socks5-hostname hermes-utilities:1000 ...`.
`/downloadPage` is server-rendered HTML (scrapable link list);
`/circularPage` is JS-loaded (links absent from the HTML — use the portal home
page notice titles instead).

## Deliverable pattern (accepted by Prakash, 2026-09-15)

**Step 1 — one master sheet:** `<YYYYMMDD>_<Project>_K-RERA_Quarterly_Update_Document_Set`,
placed in the project's RERA folder. Columns:
`Sl No | Category | Required Document | QPR Purpose | Status | File Name (Drive) | Drive Link | Notes`.
Categories: A Registration & Identity · B Approvals & Plans · C Professional
Certificates · D Financial · E Title & Land · F Sales & Inventory · G Site &
Photos · H Legal & Compliance.

Status must be **honest and action-oriented**, not just found/not-found:
`OK - available` / `REFRESH EACH QUARTER` / `NEEDS FORM 5 (currently Form 2)` /
`NOT FOUND - prepare` / `IN PROGRESS`. The refresh-every-quarter and
not-found rows ARE the deliverable's value — they're the work list.

Documents that must be regenerated **every** quarter (flag them explicitly):
architect cert, engineer cert, CA funds-utilisation cert, latest EC, current
RERA bank statements, current-quarter dated/GPS site photos, sold/unsold
statement + list of allottees.

**Step 2 — pre-filled form templates**, one Google Doc per professional, in the
same folder. Pre-fill everything knowable and leave ONLY the certification
blank:

- Header block: date line, RERA No., project name, promoter name, quarter ended
- Promoter address block ("To, The Director, …")
- Full plot description: survey/PID, katha, layout, village, hobli, taluk,
  lat/long, all four boundaries, area in sq.m
- Sanctioned drawing no. + project no. + building licence no.
- Consultant roster (architect, structural, MEP, QS/site supervisor)
- Cost totals (land / development / total) and **all three RERA bank accounts**
- Signature block with the professional's name, licence no., address, contact

Leave blank: work-done percentages, cost incurred, site-inspection date,
Table values, UDIN (CA), signature/place. Add a small italic line naming the
professional the template is prepared for.

**Step 3 — wire the template links back** into the master sheet rows for the
relevant certificates.

## Building the form docs (verified)

- Import HTML straight to a native Google Doc:
  ```python
  media = MediaIoBaseUpload(io.BytesIO(html.encode('utf-8')), mimetype='text/html')
  drive.files().create(
      body={'name': name, 'mimeType': 'application/vnd.google-apps.document',
            'parents': [FOLDER]},
      media_body=media, fields='id,name,webViewLink').execute()
  ```
  HTML import works. Markdown import **silently creates an EMPTY doc** — see
  `draas-drive-organization/references/markdown-html-to-google-doc-import.md`.
- **Always verify the doc is non-empty** by reading it back with the Docs API
  recursive walker. Text lives in `paragraph.elements[].textRun.content` AND
  inside table cells; a naive top-level `paragraph.get('text')` join returns 0
  and falsely signals failure. Grep the extracted text for the RERA number,
  project name and PID.
- Sheets batchUpdate nesting: `body={'requests':[ ... ]}` must close with `]}`
  before the call paren. A missing `}` yields
  `SyntaxError: closing parenthesis ')' does not match opening parenthesis '{'`
  pointing at the closing line, not the missing brace — check the request
  builders, not the last line.
- Write big script bodies to a file and run them (`write_file` + `python3 file`)
  rather than inline heredocs: literal `&` in form text (e.g. "Regulation &
  Development") trips the terminal background-guard on heredoc commands.

## Resolving the project + detail_id on the portal

1. POST `/projectViewDetails`, form-encoded
   `district=Bengaluru+Urban&regNo2=<RERA>&btn1=Search`, through the tunnel.
   Response is 10–32 MB; parse only `table#approvedTable` rows.
2. The matching row carries the project name, promoter, status and dates.
3. The **detail_id is the anchor id** on that row: `<a id="14833" ...>`.
4. POST `/projectDetails` with form-encoded `action=<detail_id>` (NOT JSON) and
   `X-Requested-With: XMLHttpRequest` + `Referer: /viewAllProjects`.
5. Flatten the detail HTML to text and locate the tabs:
   Promoter / Land / Project / Cost / Bank / Uploaded Documents / Complaints /
   **Quarterly Updates**.

**Store the FULL registration number.** Karnataka numbers embed district and
taluk segments: `PRM/KA/RERA/1251/446/PR/050826/008859` — not
`PRM/KA/RERA/050826/008859`. Truncated numbers fail in filings.

## Ranka Amber worked example (2026-09-15)

- Registration **PRM/KA/RERA/1251/446/PR/050826/008859**
  (ACK/KA/RERA/1251/446/PR/030726/010383), portal **detail_id 14833**.
  Promoter DRA Realty Pvt Ltd. Registered 05-08-2026, completion 31-07-2029,
  status "New Project Launch", 0 complaints.
- Pre-fill data: 1,301 sq.m land (705 open + 596 covered), PID 7057785976,
  Katha 4/124, Plot 1-B, D'Silva Layout, Pattandur Agrahara, K.R. Puram Hobli,
  Bengaluru East; lat 12.979492 / long 77.750037; Block A, 20 × 3BHK,
  FAR 1.97, 22 covered parking; land ₹7,50,00,000 + development ₹6,63,81,676
  = **₹14,13,81,676**; sanctioned drawing `GBA/MDP/DDTP/0007/26-27`,
  project `GBA/BECC/0540/25-26`, licence `BBMP/CC/4247/26-27`.
- RERA bank accounts (Kotak Mahindra, IFSC KKBK0000431, 100 Feet Road HAL 2nd
  Stage Indiranagar): **100% collection 8551119387 · 70% designated 8551119394
  · 30% operative 8551119370**.
- Architect Ar. Anjali Mandhyan CA/2018/100260 (bk@findingform.design);
  Engineer Loganathan M, SLVS Design Consultants LLP,
  BCCL/BL-3.6/E-0293/24-25; structural Manoj Kumar Reddy.
- Deliverables: master sheet `1inA_CTOtRVw76v0WyB7w3zCEfyRL2-FsZ2wKZKfdahQ`;
  Form-5 doc `1sRToV4VmuEgsez0frn_vG02ULTm-HztSaVVzPamsPAA`;
  Form-6 doc `12avTiKJ7g0aGY4oYePBKGVh81Rvbq0bFgK5CcTHX2lo`;
  Form-4 doc `1u6AAi2nmfINJi5Rw4LodOSkS9mOk2__HM2c1g5mZL8k`.
- **Gaps found at first QPR** (the action list): no List of Allottees and no
  sold/unsold statement anywhere on Drive; latest EC only to 04-07-2026;
  bank statements only to Oct-2025; site photos need a current dated/GPS
  refresh; registration-time Form 2/Form 3 scans still on file where Form 5/6
  are required.
