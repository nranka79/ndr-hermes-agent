# Kelsa misc-budget analysis — engineering/execution focus (v2 methodology)

Follow-up refinement of the misc-budget analysis. User's standing rule: **misc/unbudgeted
nodes are for genuinely UNPLANNED items only — the majority of spend must be planned.**
This pass finds where planned, execution-critical engineering work was dumped to misc.

## Scope filters (user-mandated, 2026-08-07)
- INCLUDE only: civil / execution / electrical / plumbing / MEP / finishing / site work,
  roads & pavements, borewells & water, fencing, labour contracts, precast walls,
  landscape-execution, irrigation, QS/consultancy, design/architecture.
- EXCLUDE: hotel stays, travel/transport, catering, kombucha/small bills, legal/advocates,
  retail/stationery, IT/software, events, land-sale brokerage/commission.
- Only records **> ₹50,000**. Ignore every unbudgeted bill under ₹50k.
- Deliverable must link to each Kelsa record (not just names/amounts).

## Kelsa plumbing (MCP)
- MCP defaults to Demo Account 15 — **always pass `account_id: 5` (DRA)** to
  list_pipelines / search_leads / get_lead.
- Pipelines: DRA Invoice Processing = **516**; DRA PO-WO Issuing = **537**;
  DRA Project Budgets = **2033**.
- Field identifiers (verified):
  - Invoices (516): `cf_amount`, `cf_description`, `cf_vendor_n`, `cf_invoice_number`,
    `cf_invoice_date`, `cf_category1`, `cf_budget_head3`, `cf_budget_sub_head3`,
    `cf_po_number1` (linked PO), `cf_projects_budget`.
  - PO/WO (537): `cf_total_amount`, `cf_category`, `cf_budget_head`,
    `cf_project_new` (**this is the Budget Sub Head field on PO side**), `cf_jobs`,
    `cf_ponumber`, `cf_special_instruction___notes`, `cf_nature_of_order`,
    `cf_company_name1`, `cf_project_new1` (project).

## Query recipes (amount filter = `>50000`)
- Invoices: `cf_category1:Unbudgeted;cf_amount>50000`
  `cf_budget_head3:Miscellaneous;cf_amount>50000`
  `cf_budget_sub_head3:misc;cf_amount>50000`
  `cf_budget_sub_head3:Unbudgeted;cf_amount>50000`
- PO/WO: `cf_category:Unbudgeted;cf_total_amount>50000`
  `cf_budget_head:Miscellaneous;cf_total_amount>50000`
  `cf_project_new:misc;cf_total_amount>50000`
- Result counts (2026-08-07, >50k only): invoices — Unbudgeted cat 83, Misc head 30,
  subhead misc 7; PO/WO — Unbudgeted cat 14, Misc head 3, misc head 1, subhead misc 9.
- search_leads output includes the record link directly:
  `https://kelsa.io/<pipeline>/leads?current_item_id=<id>` — embed these in the doc.

## Classification heuristics (engineering vs noise)
- Vendor name alone is unreliable — ALWAYS get_lead and read description/attachments.
- Construction vendors on Unbudgeted cat (PMR, M&M, PARAMVAH, vardhan, sri samrudhi,
  Trubld, NRK cement) are almost always real site work — pull and verify.
- Westbury hospitality invoices on Misc head are nearly all BD catch-all
  (travel/hotels/gifts) — out of scope for engineering pass.
- Taal land invoices mix two types: land levelling/grading/fencing (INCLUDE) vs
  brokerage/commission (EXCLUDE) — check the Description field.
- No-PO invoices are common for site work (12 of 18 in the 2026-08-07 pass) — note in
  the doc; several had POs attached later.

## Known misc clusters (DRA)
1. Westbury BD ₹3 Cr catch-all: General Overhead → Business Development →
   Miscellaneous → Individual (all BD spend).
2. RPL "Execution → Landscape → Misc" absorbed real civil work (labour, JCB, borewells,
   waste converters, bicycle stands, grass pavers) — should be under Civil/Execution.
3. Land assets with no project budget (Serenity Estate, Taal, Sevaganapalli, Ranka Amber,
   Oasis) → everything lands on General overhead → Unbudgeted.
4. No heads exist for QS consultancy (PARAMVAH monthly) or design development (Trubld).

## Google Doc delivery (proven path)
- Build the whole doc as HTML; import via Drive API
  `files().create(body={name, mimeType:"application/vnd.google-apps.document",
  parents:[TMP]}, media_body=MediaIoBaseUpload(html_bytes, "text/html"))` — ONE call,
  no Docs API rate limits, full table formatting preserved.
- Verify tables with Docs API `get()`: paragraph text does NOT include table cells —
  walk `el["table"]["tableRows"][]["tableCells"][]["content"]` and collect text runs.
- Share editor: `DRIVE.permissions().create(fileId, body={type:"user", role:"writer",
  emailAddress})` for each recipient (Kantesh kanteshbg@draas.com, Anbu pm2.blr@draas.com).
- TMP folder id (DRA Drive): `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-` (find by name='TMP'
  mimeType folder if it changes).
