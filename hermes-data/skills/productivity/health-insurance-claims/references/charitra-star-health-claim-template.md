# Charitra Murjani — Star Health Claim Template

Patient reference card mirroring `kdr-royal-sundaram-claim-template.md`. Verified 2026-08-25 while filing monthly medicine invoices and drafting a post-hospitalisation reimbursement claim.

## Patient & policy

- **Insured:** Mrs. Charitra Murjani (also Charitra Kamath — `charitrakamath@gmail.com`); A3-202, White House Apartments, 6th Main 15th Cross, RT Nagar, Bengaluru 560032; Aadhaar 221985915401; phone 9880055634
- **Insurer:** Star Health and Allied Insurance Co. — **Star Super Surplus (Floater)** — UIN SHAHLIP22034V062122
- **Policy No. 2131112402045892** (renewal endorsed 26-09-2025; Issuing Office Code 141133, Bengaluru)
- **Earlier claim correspondence referenced Policy No. 2198111511196678** — cite BOTH if unsure; the claim-intimation emails carry the older number
- **Sum insured ₹1,00,00,000 (₹1 Cr)**, Defined Limit ₹10,00,000, Plan "Family Size 1A+2C GOLD"
- **Claim intimation ref:** CIR/2026/141133/1527709 (NEFT-details reminder sent Jan-2026 for the Dec-2025 St John's hospitalisation claim)

## Coordinator / desk contacts (no named person — use these)

- **To:** `reimbursement.blr@starhealth.in` (BLR reimbursement desk — primary)
- **Cc:** `Customer.NEFT@starhealth.biz`, patient herself (`charitrakamath@gmail.com`)
- support@starhealth.in · helpline 1800-425-2255 / 1800-102-4477 · WhatsApp chat +91 9597652225
- FROM: `ndr@draas.com` (NDR manages the policy; the Jan-2026 thread ran via Charitra's forward)

## Drive locations

- **Murjani Medical** folder: `1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V`
- **Murjani Medical Invoices** subfolder (where invoice PDFs are filed): `1l4YOlo4HCxFAWkoVMMxT1JYloPUDq79R`
- **Index sheet** "Index of Charitra Medical Expepnse Invoices" (note the typo in the name): `1g9aqYlZYcGbOZYWdeicT90cx55604e_3ZKYv0x0mf9w` — tab `Sheet1`, columns: Date of Invoice (MM/DD/YYYY) | Institute | Invoice Type | Amount | Reimbursed? | To be Claim | Additional Notes
  - "To be Claim" column F uses `=if(NOT(E<row>),D<row>,0)`; rows 21-23 historically used hardcoded numbers
  - TOTAL row sits BELOW data — **insert new rows ABOVE it** (`insertDimension` ROWS at index = first empty row after data, `inheritFromBefore: False`), then extend the TOTAL `=sum(...)` ranges and verify read-back. Do not overwrite the TOTAL row.
- **Star Health policy PDF** (in Murjani Medical): `1tuiwIo8rKEF6WcFbXwiFudN8yfaR-VeN` (240204 Charitra Star Health Policy Doc.pdf, 7 pp, includes renewal letter + schedule)
- **Star Health Reimbursement Claim Form**: `1O-TmDC2v_C-4zoDL6ilSlfpPzJB3CzmS`

## Treatment anchor (for post-hospitalisation framing)

- Active oncology treatment at **St. John's Medical College Hospital, Bengaluru** (medical oncology, Dr Annie); pembrolizumab (Keytruda) cycles, infusion confirmations from MSD
- Hospital admissions: Dec-2025 (chemotherapy; discharge Jan-2026), Mar-2026 (discharge summary 17-03-2026), ongoing 3-weekly chemo
- Monthly supportive medication **AXZYB 5MG Tab (14's)** bought from **Mythri Pharmaceuticals** (56 3rd Floor S S Arcade, 6th Cross, Wilson Garden, Bangalore 560027; GSTIN 29ACPPV1724K1ZX; ph 9845162872)
- Note: AXZYB 5MG is NOT listed on the pembrolizumab prescriptions — the pharmacy invoices alone don't prove the link to treatment. Attach the latest prescription + infusion confirmation + last discharge summary to anchor it.

## Medicine-invoice claim pipeline (verified 2026-08-25)

1. Deskew/straighten scanned invoice pages (see `ocr-and-documents` → `references/deskew-scanned-invoices.md` for sub-degree skew handling; verify upright + readable before filing)
2. Rename `YYYYMMDD_Charitra_Murjani_Medicine_Invoices_YYYYMM-MM_MythriPharma.pdf` (drive naming convention, underscores only)
3. Upload to **Murjani Medical Invoices**
4. Add one row per invoice to the **Index sheet** (above TOTAL; extend ranges)
5. Draft claim email to the desk (direct claim, NOT advisory — see SKILL.md "Key communication preferences"):
   - Subject: `Reimbursement claim - Ongoing post-hospitalisation treatment expenses (medicines) - Mrs Charitra Murjani - Policy 2131112402045892`
   - Attach: invoice PDF + latest Rx (+ prior month Rx) + latest infusion confirmation + last discharge summary (~11 MB total for 5 PDFs)
   - Body: HTML with invoice table, state total claimed, ask to register claim / return claim number; mention CIR/2026/141133/1527709 for continuity
   - Draft only via raw Gmail API (raw MIME with MIMEBase attachments); user sends from Drafts