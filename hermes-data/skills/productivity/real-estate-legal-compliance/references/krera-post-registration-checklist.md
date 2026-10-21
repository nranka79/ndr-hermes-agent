# K-RERA "Checklist for Post Registration – Apartments" — replica + fill

**Trigger.** NDR forwards Prakash's quarterly-update email and says some variant of
*"there is a checklist for post registration apartment … series of tables in three columns,
the third column is empty and that's where we fill the details … fill it in, make it in
HTML/CSS, let me see the HTML version, then we'll PDF it."*

This is the **fourth** K-RERA quarterly document, alongside Form-4 (CA), Form-5 (Architect)
and Form-6 (Engineer) — see `krera-qu-forms-html-replica.md` for the replica mechanics
(fixed A4 sheet, print page-breaks, publish to DRA Content, self-contained copy to Drive),
which apply unchanged here. What is different is the *document shape* and the *data map*.

Verified end-to-end on Ranka Amber, Q2 FY 2026-27 (21 pp, `DRA-ART-2026-000048`).

---

## 1. The source is a KRERA print, not a scan — and it has FOUR columns

The PDF Prakash sends is a browser print of the KRERA portal checklist. It has a full text
layer. Its tables are **four** columns, not three:

```
Sl. No | Field Name | Description | <EMPTY>
  x≈70    x≈95.5       x≈243       x≈394.5    (right edge ≈546 pt on A4)
```

NDR perceives this as "three columns" because he reads Sl. No as part of the field column;
the *empty* fourth column is the one he wants filled. Do not add a column — populate the
one that is already there and leave the header wording alone.

**Extract the structure from the ruling lines, not from the text run order.**

```python
import fitz
d = fitz.open(src)
for pi, p in enumerate(d):
    xs, ys = set(), set()
    for dr in p.get_drawings():
        for it in dr['items']:
            if it[0] == 'l':
                a, b = it[1], it[2]
                if abs(a.x - b.x) < 0.5: xs.add(round(a.x, 1))
                if abs(a.y - b.y) < 0.5: ys.add(round(a.y, 1))
            elif it[0] == 're':
                r = it[1]; xs |= {round(r.x0,1), round(r.x1,1)}; ys |= {round(r.y0,1), round(r.y1,1)}
```
Vertical x's cluster to ~70 / 95.5 / 243 / 394.5 / 546. Bucket every word bbox centre into
those bands, group rows by `round(y0/4)*4`, and you get the whole checklist as data. Rows
wrapped across lines belong to the previous row — merge, don't duplicate.

## 2. The 21-page section map (Ranka Amber instance)

| pp | Section |
|----|---------|
| 1 | Project Details |
| 2 | Promoter Details – **Individual** |
| 3 | Promoter Details – **Company** |
| 4 | Promoter Details – Partnership |
| 5 | Promoter Details – Societies |
| 6 | Promoter Details – Development/Public/Government Authority |
| 7 | Saleable Unit |
| 8 | Project Schedule – Civil Works |
| 9 | Project Schedule – Internal Infrastructure |
| 10 | Project Schedule – External Infrastructure |
| 11 | Project Schedule – Common Areas |
| 12 | Land Cost – Plot Land Cost Details **+** Land Cost – JDA Details |
| 13 | TDR Cost **+** Approval Cost (rows 1–8) |
| 14 | Approval Cost (rows 9–10) **+** Construction Cost |
| 15 | Civil Works **+** Bank Details |
| 16 | Tower Details **+** Infrastructure, Amenities & Common Areas **+** Status of Approval and NOC's (1–10) |
| 17 | NOC's (11–12) **+** Litigation Details **+** Modification Plan |
| 18 | Association of Allottees **+** Construction Worker's Welfare Fund Registration |
| 19 | Construction Cost *(a repeat of p14 — a KRERA artefact, keep it)* |
| 20 | Construction Cost Details **+** Final Approvals |
| 21 | **blank in the source** |

A 20-unit project needs ~200 mm of paper per page, so **split the fat pages** rather than
shrinking type. In this build p16 (Tower + Infra + NOC) overflowed to 295.5 mm and had to be
split into p16 (Tower + Infra) and p17 (NOC), producing 21 content pages against the source's
21 (the source's last is blank). Decide the pagination *after* measuring, not up front.

## 3. Fill conventions NDR uses for this document

- **Promoter type sections that don't apply are filled, not dropped.** Pages 2/4/5/6 get
  `Not Applicable` on every row **plus a one-line reason** ("promoter is a Private Limited
  Company, not a partnership firm"). Deleting them reads as an omission to a reviewer.
- **Project Schedule – Civil Works → `Turnkey`** against every head and sub-head
  (Sub-structure, Super-structure, Masonry, Finishing/Interior and all 7 sub-items).
- **Project Schedule – Internal Infrastructure → `NA`** on all 11 heads.
- **Project Schedule – External Infrastructure → `Any`** on all 10 heads. NDR's dictation is
  ambiguous ("any NA except sewage and drain … just put any everywhere completely any") — fill
  all `Any` and **ask** whether Sewers & Drainage / Storm Water Drains should be `NA`.
- **Common Areas** mix freely: `Not Started` for staircase/lift/lobby/fire-escape/entrance/
  foyer/terrace/outer-wall; `Any` for basement / management-staff provision / water
  conservation; `Completed` for water tanks & sumps; `NA` for open parking areas and fans.
- **TDR Cost → `NA`** throughout when no TDR was purchased.
- **Construction Cost – Principal sum and interest → `Nil`** (no borrowings / no mortgage),
  with a short parenthetical. Do not leave it blank.
- **Litigation / Modification / Association → `NA`** (and `No` for the yes/no heads).
- Amounts withdrawn from the designated bank for approvals and for civil works → **`Nil`**,
  because nothing was collected. Say *why* in the cell — it looks like an error otherwise.

## 4. Where every figure actually lives (Karnataka project, post-registration)

This map is reusable for Form-4/5/6 too, not just the checklist.

| Figure | Authoritative source |
|---|---|
| Project name, type, status, address, start/end, lat-long, boundaries | KRERA portal **SIS 5.2 spreadsheet** (`Project details` tab) |
| **Land / approvals / construction cost split** declared to RERA | **CA Form Reg-1** ("Chartered Accountant's Certificate (Registration)"), page 4 cost table — *this is the one to use* |
| Engineer-certified construction cost | Cost Abstract + Form 3 (engineer's certificate) |
| Unit-wise RERA carpet, exclusive common area, common area to association, UDS, parking | SIS 5.2 **`Area details`** tab (one row per unit) |
| Totals: built-up area, carpet, FAR, coverage, plinth, plan-approval no. & date, water source, covered parking | SIS 5.2 **`Plan details`** and **`FAR Details`** tabs |
| Company: CIN, PAN, GSTIN, incorporation, directors + DINs, net worth | CA Form Reg-1 pages 1–2 ("Additional Details of the Promoter") |
| Designated bank accounts (100% / 70% / 30%) | CA Form Reg-1 page 3 |
| JDA share ratio, unit split, registration no., landowner names/address/email/mobile | JDA **plus** the supplementary sharing agreement |
| Land cost as per guidance value | the promoter's letter to KRERA confirming total cost of project land |
| Commencement / plinth status | the promoter's *Declaration on Commencement Certificate* filed at registration + the BBMP certificate itself |
| Site supervisor / QS / professional identities | Form-2 (architect), Form-3 (engineer), area statement |

Ranka Amber figures for reference: land **Rs 7,50,00,000**, approvals **Rs 74,06,075**
(plan 14,06,075 + water 30,00,000 + electricity 30,00,000), construction **Rs 5,89,75,601**
(engineer 5,69,75,601 + consultant fees 5,00,000 + admin 15,00,000), **total Rs 14,13,81,676**.

## 5. The hard part: conflicting figures. Prefer the RERA-declared value, flag the rest.

The same quantity exists at two or three different values across the record. **Never silently
pick one.** Use the RERA-declared figure and surface every divergence to NDR in the covering
message — he verifies figures and will ask.

| Field | Candidates seen | Which to use |
|---|---|---|
| Land cost | Rs 7,50,00,000 (RERA/CA Form Reg-1) · Rs 7,54,46,000 (guidance-value letter arithmetic) · Rs 7,08,84,000 (JDA market value in the EC) | the RERA-declared one |
| Carpet area | 2,225.08 sq.mt (RERA-registered total) · 2,165.00 sq.mt (sum of the per-unit column) | the registered total; note the sum |
| Parking | 22 covered (sanctioned plan + project-details letter) · 20 (per-unit column, 1 each) | the plan figure; note the column |
| UDS | 1,300.62 sq.mt (column total) · 1,300.58 sq.mt (land extent) | the column total; note the 0.04 |
| **% of completion** | **4.95%** = Rs 70,00,000 ÷ Rs 14,13,81,676 (project level, Form-4 item 7) · **12.29%** = Rs 70,00,000 ÷ Rs 5,69,75,601 (building level, Form-6 Table A) | both are defensible — **name which you used and warn that KRERA must hear one consistent number across the pack** |

## 6. BBMP Commencement Certificate vs Plinth Certificate — get this right

NDR will often say *"commencement certificate obtained"* when what is actually on the record is
the **Plinth Certificate**. Do not just accept the framing.

- Under BBMP rules the **Commencement Certificate issues only after the plinth (including
  basement) is completed**. Projects file a **"Declaration on Commencement Certificate"** with
  KRERA at registration promising to upload the CC **during the quarterly updates**.
- The **Plinth Certificate** is the precursor and carries its own number format, e.g.
  Ranka Amber `GBA/BECC/0540/25-26/PC/01/New`, on LP `GBA/MDP/DDTP/0007/26-27`, issued by
  DDTP (Mahadevapura) under **s.239 of the GBG Act 2024**, after a site inspection.
- The plinth-certificate **fee is an approval cost** and belongs in the Approval Cost table
  (Ranka Amber: Rs 61,899, transaction receipts `BBMP/EoDB/RC/…`).
- So: fill the NOC row with the **plinth** certificate number, its issue date, and the
  declaration position — then ask whether a CC has in fact been issued.

The plinth certificate is also the best source for the **structural facts**: it restates the
sanctioned configuration ("1 Stilt + 1 Ground + 3 Upper Floors, 20 dwelling units"), which is
where the "5 slabs of super-structure" (stilt slab + 4 floor slabs) and "0 basements / 1 stilt"
answers come from. Read it before filling the Saleable Unit and Tower Details tables.

## 7. Delivery and verification

Same as the other replicas, with two additions:

1. Build → publish to **DRA Content** → build the self-contained copy (inline the CSS and JS,
   assert no external refs remain) → file into the project's RERA folder on Drive.
2. **Verify the published payload**: `GET /api/artifacts/<id>/versions` and check
   `size_bytes` equals the sum of the local files, and `file_count`.
3. **Verify the Drive copy by reading it back** and comparing sha256 — a create() that returns
   an id is not proof the bytes landed.
4. Make the Drive upload idempotent: query `name = '…' and '<folder>' in parents and trashed =
   false`, delete any hit, then create. Re-running the job must not leave two copies.
5. **No PDF until NDR confirms.** He reviews the HTML first ("once we analyze it and confirm,
   then we will make it PDF again").

## 8. Phrase the gaps as numbered questions

Every time this document was built, the deliverable that landed was *the filled form plus a
numbered list of what could not be determined*. NDR expects it:

- ASR / stamp-duty figure for the Approval Cost rows (take it from the JDA registration record)
- the website URL, if NDR supplied one rather than a confirmed live domain
- the HOD/director mobile (the RERA letterhead number may be a switchboard, not a personal one)
- **office address** — NDR may name an operational office (e.g. Prizm Greystone, Cunningham
  Road — the group's design/coordination office, also the architect's address) while the
  *registered* office on the CIN and in the RERA filing is different (Queens Corner, Queens
  Road). Fill what he asked for, show the registered office underneath, and ask which stands.
- whether a brochure exists (a "Declaration on No Brochure" at registration does not preclude
  a brochure PDF existing on Drive now)
- Construction Worker's Welfare Fund (BOCW) applicability, and project insurance
