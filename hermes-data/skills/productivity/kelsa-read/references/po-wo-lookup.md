# PO / Work Order Lookup in Kelsa (DRA)

Recipe for "get me the purchase order / work order for <vendor> for <project>" in the DRA Kelsa account.

## Pipelines (DRA account = ID 5)

| Pipeline | ID | Item | Use |
|---|---|---|---|
| DRA PO-WO Issuing | 537 | PO-WO | POs/WOs proposed → approved → Signed & Issued. The `Issued PO-WO` field holds the issued PDF (S3 presigned URL). |
| DRA Invoice Processing | 516 | Invoice | Invoices submitted against a PO-WO until payment/rejection |
| DRA Vendor Shortlisting | 531 | Vendor | Vendor selection / shortlisting |
| DRA Purchase Order Details | 7954 | PO details | Line items of a PO |
| DRA Materials Receipt | 514 | Arrival | Goods receipt against POs |

## Lookup steps

1. `list_accounts` → pick **DRA (ID 5)** (default Demo Account 15 / ID 1 is NOT DRA — never search there for real data).
2. `list_pipelines(account_id=5)` → confirm 537 (PO-WO Issuing).
3. `search_leads(pipeline_id=537, query="<vendor-name>")` — vendor name works as a freetext search (matches `Vendor New` / narration). Example: `query:"SLVS"` returned the record; `query:"SLVS DESIGN"` also matches.
4. `get_lead(pipeline_id=537, lead_id=...)` — full record: Vendor, Project, PO/WO ref (`Po Number New` / `PONumber`), amounts (`Total Value of Order (Without Tax)`, `Total Tax`, `Total Amount`, `Advance To Be Paid`, `Invoiced amount`), `Issued PO-WO` S3 URL, stage, approvers (from Recent Activity), followers.
5. Download the issued PDF from the `Issued PO-WO` field URL: `curl -sL -o /tmp/wo.pdf "<url>"`.
6. If `pdftotext` returns empty → it's a scanned PDF (bizhub KONICA scans are common — `pdfinfo` shows Producer: KONICA MINOLTA). Render pages: `pdftoppm -f N -l N -r 120 -png /tmp/wo.pdf /tmp/page` then `vision_analyze` each PNG with a targeted question ("commercial breakdown / fee / milestones"). Page 1 usually identifies the doc (WO ref, parties); page 2 scope; page 3 commercials.

## Vendor background / contact lookup

When the user asks "is <vendor> registered / what's their contact person & phone / since they're a registered vendor..." — the vendor master is **DRA Vendor Shortlisting (pipeline 531)**, NOT the PO pipeline.

1. `search_leads(pipeline_id=531, query="<vendor-name>")` — vendor name freetext works (e.g. `"SLVS"` → the SLVS DESIGN CONSULTANTS LLP record).
2. `get_lead(pipeline_id=531, lead_id=...)` — the vendor record carries:
   - `Key Contact Name` (e.g. Mr.Loganathan)
   - `Key Contact Designation` (e.g. Managing Director)
   - `Key Contact Mobile` (e.g. +919008917182)
   - `Vendor Offerings` (e.g. Consultancy Services)
   - `Vendor Source Information` (e.g. "Referred by Mr.Kantesh")
   - Followers often include the internal sponsor (Anbarasan, Kantesh B G...)
3. A vendor can be in early stage (Prospect) but already have POs — stage on 531 is NOT a blocker for having been issued work. Cross-reference with 537 when the user pairs "vendor + PO".

## Recording a follow-up agreement on the PO

When a fee revision / settlement is agreed AFTER the PO was issued (e.g. architect fee negotiation), NDR wants the agreed terms captured as an internal note ON the original PO record — paired with the confirmation email draft to the vendor. Use `kelsa_call_tool(tool_name="add_note", arguments={"pipeline_id": 537, "lead_id": <PO lead id>, "text": "..."})`. Keep the note self-contained: supersedes the original WO reference, each agreed component with its arithmetic logic, payment-term changes (which phases), GST applicability, and "email confirmation sent <date>". Present the note text to NDR for approval BEFORE posting (see email-drafter → references/fee-proposal-comparison.md "Draft-note-first workflow").

## Pitfalls (also applies to vendor records)

- **Person-name search fails when the PO keys on the firm name (confirmed 2026-08-25, A.J. Architects):** `search_leads(pipeline_id=537, query="Arvind")` returned **0 results** — the PO record for architect Arvind Jain is stored as vendor **"A.J. Architects"** (`Po Number New: Dra realty pvt ltd.-A.J. Architects`, PO 594, project General overhead). Searching "Jain" ALSO fails to find it (it matches unrelated POs from Hitendra Jain's recommended surveyors). Fix: search by the FIRM name token ("Architects", "A.J.") or cross-search the vendor shortlisting pipeline 531 for the person's name (`"Arvind"` → 2 vendor records: "Arvind Jain Architect" retired + "A.J. Architects" prospect), get the vendor's `Key Contact Name`, then search 537 by the matching firm token. Verify the `Vendor New` field on the result before declaring a hit.
- **Architect consultant POs may sit in "General overhead" project** (PO 594 = A.J. Architects, Project: General overhead, Category: Unbudgeted) — a project-name search ("Allalsandra", "North Star") returns 0 for them. Search by vendor/firm token, not project.

- **S3 presigned URL expires in 7 days** (`X-Amz-Expires=604800`). If the user wants a durable copy, download → upload to Drive with the standard naming convention BEFORE the URL dies. Deliver the Drive link, not the transient S3 link.
- **Voice transcription of vendor/project names** — search the pipeline with the raw spoken token AND likely expansions (e.g. "Anbar" = Anbarasan approver, "MVP" may not be a project on the PO). Don't assume every project name in the user's ask maps to a separate PO; confirm from the record's `Project` field.
- **The PO record's displayed name may be just a number** (e.g. "753") — the real identifier is `PONumber` like `Dra realty pvt ltd.-<VENDOR>-753`. Trust the fields, not the headline name.
- **Approvals live in Recent Activity**: lookup shows who approved (e.g. "Nishant Ranka — stage changed to Signed & Issued", HoD names) — use it to answer "who signed this".

## Worked example (2026-08-25)

"PO for SLVS construction for Ranka, Anbar, MVP" → `search_leads(pipeline_id=537, query="SLVS")` → 1 result, lead 54108669 (display "753", Signed & Issued). `get_lead` → vendor **SLVS DESIGN CONSULTANTS LLP**, project **Ranka amber**, WO ref DRA/AMBER/WO/2026-27/002, MEP Design Consultancy, ₹2,75,000 + ₹49,500 GST = ₹3,24,500, advance ₹82,500, approvers: Anbarasan (HoD) + Nishant (Chairman). PDF is a 4-page KONICA scan → pdftoppm + vision OCR gave WO ref/parties (p1), scope PHE+Electrical excluding liaisoning (p2), fee ₹2,75,000 + milestone schedule 25/30/30/10/5% (p3).