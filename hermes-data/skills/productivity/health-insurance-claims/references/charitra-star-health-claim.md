# Charitra Murjani — Star Health Claim Reference

Worked example (25-Aug-2026): post-hospitalisation medicine reimbursement claim, built and verified as a Gmail draft.

## Policy facts
- **Insurer:** Star Health And Allied Insurance Co. Ltd
- **Plan:** Star Super Surplus (Floater) — UIN SHAHLIP22034V062122
- **Policy No:** 2131112402045892 (renewed 26-Sep-2025)
- **Sum insured:** Rs. 1,00,00,000 (₹1 Cr); Defined Limit ₹10,00,000; Family 1A+2C GOLD
- **Insured:** Mrs Charitra Murjani (White House Apartment A3-202, 6th Main 15th Cross, RT Nagar, Bengaluru-560032; Aadhaar 221985915401)
- **Earlier claim refs:** Policy 2198111511196678; Intimation No. CIR/2026/141133/1527709 (NEFT-details reminder Jan-2026)

## Coordinator contacts (the desk "we have written to earlier")
- To: `reimbursement.blr@starhealth.in` (Star Health Bengaluru reimbursement)
- Cc: `Customer.NEFT@starhealth.biz`, Charitra Kamath <charitrakamath@gmail.com> (forwarder of intimation mails)
- Toll-free: 1800-425-2255 / 1800-102-4477; support@starhealth.in
- No named coordinator found in Gmail/Vault threads — the WhatsApp attachment in the thread is just the WhatsApp logo (useless for names). Always address the desk, not a person.

## Where Charitra's medical records live
- Drive: **Murjani Medical** folder `1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V`; **Murjani Medical Invoices** subfolder `1l4YOlo4HCxFAWkoVMMxT1JYloPUDq79R`
- Expense tracker: **"Index of Charitra Medical Expepnse Invoices"** sheet `1g9aqYlZYcGbOZYWdeicT90cx55604e_3ZKYv0x0mf9w` — single tab Sheet1; headers: Date of Invoice (MM/DD/YYYY) | Institute | Invoice Type | Amount | Reimbursed? | To be Claim (F col = `=if(NOT(E),D,0)`) | Additional Notes; TOTAL row at bottom. When appending: insert rows BEFORE the TOTAL row via `insertDimension`, then extend the TOTAL formulas (`D=sum(D2:D26)`, `F=sum(F2:F26)`) — the old D formula only summed 2:20, silently excluding rows 21-23. Flag any total-behavior change to NDR.
- Filing convention: `YYYYMMDD_Charitra_Murjani_Medicine_Invoices_YYYYMM-MM_MythriPharma.pdf` (underscores only).

## The 25-Aug-2026 claim (worked example)
- **3 Mythri Pharmaceuticals invoices, all AXZYB 5MG Tab (14's)**, ongoing monthly medication:
  1. Inv 26001730010422 · 06-Jul-2026 · ₹2,012
  2. Inv 26001730012146 · 22-Jul-2026 · ₹4,020
  3. Inv 26001730014236 · 10-Aug-2026 · ₹4,020
  - Total: **₹10,052**
- **Framing (direct claim, per NDR rule — see SKILL.md):** ongoing post-hospitalisation treatment at St. John's (medical oncology, pembrolizumab/Keytruda), medicine claim submitted; ask to register and reimburse to NEFT on record + return claim number.
- **Attachments (5):** (1) deskewed invoice PDF; (2) Pembro prescription 12-08-2026 St John's `1nMQl8qbJamZcTaF0OnSFlVaawjaUPLQv`; (3) Keytruda infusion confirmation 12-08-2026 MSD `1UC9A1wMS5SGMOnh8H9u5IEAjvHDFZzUI`; (4) Pembro prescription 01-07-2026 `1rPed282daUwmSipdjXm_QEKdDnK73ywi`; (5) Discharge summary 17-03-2026 `1H027eI9kI8oqfJrQK6b45S7kDtj4Cm9h`.
- **Realism check to give NDR:** Jul–Aug invoices fall OUTSIDE the usual 60–90 day post-discharge window from the Mar-2026 admission, and AXZYB isn't a listed chemo drug in the attached prescriptions — Star Health may refuse. That is the intended "let them refuse" outcome; escalate via Stage 7 if they do.

## Email build pattern
- Raw Gmail API draft (never send): MIMEMultipart('mixed'), HTML body w/ invoice table + navy header, PDF attachments via MIMEBase base64; delete prior draft with same subject before recreating; verify To/Cc/Subject/attachments after creation.
- Draft id created: `r6536662570200815679` (25-Aug-2026; replaced the earlier advisory draft).