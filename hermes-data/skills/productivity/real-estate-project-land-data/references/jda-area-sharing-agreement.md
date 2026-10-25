# JDA Area-Sharing / Area-Allocation Agreement — lookup & extraction

The registered instrument that fixes saleable area, the sharing ratio, **unit-wise allotment** and
parking allocation for a JDA project. Trigger phrasing: *"extract the registered area sharing /
area allocation agreement for the JDA where we have received approved building now"*, "the sharing
agreement for the JDA", "who gets which flats in \<project\>", "area allocation agreement".

Verified 2026-09-19 on Ranka Amber.

## 1. Locate — search ladder

Run from `terminal()` with the right identity (`HERMES_SESSION_USER_ID=<uid>` + service_name
`google-draas`); the vault socket is not available inside `execute_code`.

```python
svc.files().list(q=..., pageSize=100, fields='files(id,name,mimeType,size,createdTime,owners)',
                 corpora='allDrives', includeItemsFromAllDrives=True, supportsAllDrives=True)
```

The filename does NOT contain "area sharing". Query in this order:

1. `name contains 'Sharing'` / `'Sharing Agreement'` / `'Supplementary'`  ← **the winner**
2. `name contains 'JDA'`, `'joint development'`, `'Addendum'`
3. `fullText contains 'area sharing'` / `'area allocation'` / `'share of built up area'`
   — fullText is a **noisy net**: it returns every IRR model, DPR and enterprise-data sheet that
   merely mentions the phrase. Use it to discover, never to conclude.
4. `name contains '<Landowner surname>'` (e.g. `'Raghu'`, `'Iyer'`) — landowner-named docs surface
   the KYC/OCI/EC family and the JDA itself.
5. `name contains '<Principal JDA reg no>'` (e.g. `'2227'`) — finds the registered Principal JDA copy.

**Zero hits on 'area sharing' / 'SSA' is expected and is NOT a miss** — the document is titled
*Supplementary Sharing Agreement*. Never report "not found" from the phrase searches alone.

**Expect TWO originals** — one signed copy filed per party (`..._Signed_Copy_For_DRA.pdf`,
`..._Signed_Copy_For_Raghu.pdf`), same date, near-identical. Verify both are substantively the same
(see §3) and deliver the one belonging to the requesting party.

## 2. Extract — these are scans

`pdftotext` returns ~15 chars. Full pipeline:

```bash
pdftoppm -r 200 -gray -png doc.pdf ocr/doc          # 15 pages, ~20s
for p in ocr/doc-*.png; do echo "---PAGEBREAK $p" >> ocr/doc.txt
  tesseract "$p" stdout --psm 3 >> ocr/doc.txt; done
```

`--psm 3` matters (default psm returns empty on some legal scans). OCR quality on these ~8.5 MB
scans is mediocre — expect and tolerate:
`tights`→`rights`, `SANCCTION`, `TF3`→`aF3`, `379.77` for `579.77`. **Do not quote a number from a
single garbled cell** — recompute checksums instead (§3).

Read pages in order; the document is a fixed shape:
- p1 parties + date + execution place
- p2 recitals + Schedule A reference (Principal JDA + Addendum reg. nos.)
- p2-4 sanction details, project name, **sharing ratio**, **total saleable area**, LO allotment table
- p4 **Developer allotment table**
- p5-7 operative clauses (deviation, deficit/excess, parking, alienation, possession, POA bar)
- p8-12 Schedules A–D (property description, area statement, car parking, BBMP sanction block)
- p13+ annexures (building-plan scan, stilt parking layout)

### Navak sentence to pull verbatim
The recital states the purpose precisely: *"the parties now wish to record herein the final and
agreed terms of sharing of the built-up area, apartment allotments, parking allocations, and other
incidental matters."*

## 3. Verify before reporting (mandatory)

- **Cross-check the total.** Sch B unit super-BUAs were transcribed as 11,976.00 per side → ×2 =
  23,952, but the document states total saleable **27,544.00 sq ft**. This is a real document
  inconsistency, not an OCR defect — the Schedule B table appears to omit balcony / common-area
  loading (cf. the customer area statement's separate `Balcony/Exclu` and `Common Area Loading`
  columns). **Report both figures and name the basis; never silently pick one.**
- **Verify per-unit arithmetic** where possible — UDS per unit should reconcile against total plot
  area (Amber plot ≈ 1,300.58 sq.m; ΣLO UDS ≈ 8,640 sq ft → ≈ 0.4395 UDS/sqft of super-BUA, which
  matches the area statement's stated factor).
- **Diff the two signed copies** (normalize + strip blank lines, `difflib.unified_diff`). Amber's two
  copies differ only in scan artifacts and one character (`tights`→`rights`, `13"`→`13`). Report them
  as substantively identical — that is a useful assurance, not noise.
- **Confirm the registration/stamp position.** Say plainly whether the copy on Drive is the
  *registered* instrument or an executed-but-pre-registration copy — read clause on stamp duty &
  registration (Amber: Developer bears both; executed in duplicate, one original retained per party
  *after registration*) and look for a registration endorsement / stamp certificate page. Do not
  claim "registered" if only the execution is evidenced.

## 4. What to deliver

Deliver **the document itself** (MEDIA: the PDF) plus a structured read: parties + capacity (incl.
SPA/GPA numbers), the sanction it binds to, ratio, total saleable area, both allotment tables,
parking split, and the protective clauses. Then flag discrepancies. This is a legal-instrument
lookup — the file is the deliverable, the summary is the value-add.

## 5. Pitfall — floor attribution drifts between documents

**The registered SSA's floor labels and the marketing/customer area statement's floor labels often
disagree.** Amber (verified):
- SSA: LO = 101-105 (Ground) + **401-405 (Third)**; DEV = 201-205 (**First**) + 301-305 (**Second**).
- Customer Area Statement: 201-205 labelled **Second**; 301-305 labelled **Third**; LO on
  **Fourth**.
- Strata model already in use elsewhere: LO = 001-005 + 301-305; DEV = 101-105 + 201-205.

Three different numbering schemes for the same 20 units. **The registered SSA governs** (it is what
banks, RERA and the sub-registrar see), and the SSA's own Schedule B is internally self-consistent.
Before either document goes to a bank or KERA, reconcile the floor label against Schedule B of the
SSA. Do not renumber anything yourself — surface the conflict with both sources named.

Also expect a small **rounding gap between the SSA and the internal statements**: SSA states
`saleable 27,544.00`; Amber's customer area statement notes `27,543.25`. Quote the registered figure
as on-record and note the internal figure alongside.

## 6. Ranka Amber — verified facts (2026-09-19)

- **Documents** (owner ndr@draas.com, 15 pages each, scans):
  - `20260624_RankaAmber_SupplementarySharingAgreement_Signed_Copy_For_DRA.pdf` —
    `1Ygo5p4JUUYswnwJffLS6Z9IpAnQyCkIU`
  - `20260624_RankaAmber_SupplementarySharingAgreement_Signed_Copy_For_Raghu.pdf` —
    `1IkNoLeNVCtOtgxFDbWW0MNRVmqGG1eUE`
- **Executed** 24.06.2026 at Bangalore.
- **Parties:** LANDOWNERS — Mrs. Farida R Iyer (via SPA holder Mr. Raghu Iyer, GPA
  `DRO/SJN/GPA/1088/2025-2026`, adjudicated 12.08.2025) **+** Mr. Raghu Iyer alias Raghunathan Iyer.
  DEVELOPER — M/s DRA Realty Private Limited (CIN U70100KA2011PTC058105), Director Mr. Nishant
  Dinesh Ranka.
- **Principal JDA:** registered Document No. **SHV-1-02227-2025-26**, dt. 16.08.2025, Sub-Registrar
  Shivajinagar + Addendum same date (amends the Super Built-up Area definition, inserts Clause 9
  Marketing & Sales). Drive copy of the registered JDA:
  `Copy of 20250816 JDA Reg N0 2227(2025-26).pdf` = `1cgQQ5nsN_AwaKPwVcH_iBxSBgJj1Jxl0`.
- **Sanction:** BBMP **LP No. BBMP/CC/4247/26-27**, licence 27.04.2026, acceptance 07.05.2026, DDTP
  Mahadevapura. GBA File No. **GBA/MDP/DDTP/0007/26-27**. Validity 5 yrs. Total land 1,300.58 sq.m.
  Stilt + G + 3, 20 apartments, Block A.
- **Ratio 50:50** (Landowners : Developer); total saleable **27,544.00 sq ft (2,558.9 sq m)**.
- **LO (10):** GF1-5 = 101-105, TF1-5 = 401-405. **DEV (10):** FF = 201-205, SF = 301-305.
  Each side 11,976.00 sq ft built-up / 11,652.00 sq ft RERA carpet.
- **Parking 22 stilt slots:** LO green 1,3,5…19 (10) | DEV yellow 2,4…20 (10) | visitor 21,22 (2).
  Layout = Annexure II Drawing No. 150201 dt. 25.03.2026.
- **Protective clauses:** 10(b) LO always ≥50%, deficit made good by Developer at no cost;
  10(c) excess shared equally; 14 future additional floors 50:50; 15 possession within 30 months of
  RERA registration, target **07.11.2028**; 17 **no irrevocable POA** — Developer sells LO units only
  on LO's written instructions; 23 stamp duty + registration solely Developer; 24 SSA prevails over
  Principal JDA/Addendum on conflict; 26 executed in duplicate, one original per party after
  registration.
- **Related Drive docs:** `Ranka Amber - Customer Area Statement.pdf` =
  `1yZEj1HhGOujhdflwtgtVGYn_TLjycldQ`;
  `Ranka Amber - Common Area and amenitie area statement 27626.pdf` =
  `1uJliH0jHWOEEZgB2ZHQjK2Yu-6Cypk4i` (architect Ar. Anjali Mandhyan, Finding Form Design Studio,
  COA CA/2018/100260, certified 22.06.26);
  `Ranka Amber - Architect Certificate - Area Statement.pdf` = `1rXlat69325nKxbjd-zActdYPm-CvkABH`;
  `Ranka Amber - Execution Plan Area Statement April 2026` = `1PKzB3CCSKZvWpxkcKAVBhI8XGnj626_ax5w9yvvLy3U`.
- Note: `20250810 JDA Raghu Iyer Whitefielf 14K sqft` = `1i8rOWUVsJNlNC6zSLqn6_i-se1gf1POJ_vMIt4tVIuY`
  is the same deal's earlier JDA working copy (14,000 sqft plot).
