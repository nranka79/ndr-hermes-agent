# Charitra Murjani — Star Health & Medybiz/KIRAN PAP (references)

Load this before any Charitra Murjani medical-invoice filing, Star Health reimbursement,
Medybiz/KIRAN PAP infusion confirmation, or post-hospitalisation claim task.
Verified 2026-08-28.

## Patient / family

- Charitra Murjani ("Chinks"); A3-202 White House Apartments, 6th Main 15th Cross, RT Nagar,
  Bengaluru 560032; phone 9880055634; Aadhaar 221985915401.
- Her email for insurer/Kiran forwards: **charitrakamath@gmail.com** (verified from Gmail thread headers).
  Also charitra_murjani@yahoo.com on some older docs.
- **Roshni Murjani:** rmurjani@gmail.com (on all Medybiz thread CCs).
- NDR manages her treatment/insurance; Roshni Ranka (rnr@draas.com) also in the loop.
- Ongoing oncology treatment (ASPS sarcoma) — Keytruda/Pembrolizumab infusions; St John's
  (Dr Annie K Baa — Medical Oncology, Associate Professor), AIIMS second opinion.

## Policy (Star Health & Allied Insurance)

- Star Super Surplus (Floater), UIN SHAHLIP22034V062122.
- Policy No **2131112402045892** (renewal letter 26-Sep-2025); earlier claim correspondence used
  Policy No **2198111511196678**.
- Sum insured **₹1,00,00,000 (₹1 Cr)**; Defined Limit ₹10,00,000; family size 1A+2C GOLD (Floater).
- Prior claim: **Intimation No CIR/2026/141133/1527709** (Dec-2025 hospitalisation; NEFT-details
  follow-up email 20-Jan-2026). Dec-2025 St John's chemo claim approved ₹2,42,860.
- Coordinator = Star Health Bengaluru reimbursement desk:
  - `reimbursement.blr@starhealth.in`
  - `Customer.NEFT@starhealth.biz`
  - support@starhealth.in · toll-free 1800-425-2255 / 1800-102-4477
  - Only one Star Health thread in NDR accounts (Charitra's forward of the NEFT reminder).

## Pharmacy

- Mythri Pharmaceuticals, 56 3rd Floor S S Arcade, 6th Cross Wilson Garden, Bengaluru 560027;
  GSTIN 29ACPPV1724K1ZX; phone 9845162872. Monthly AXZYB 5MG Tab 14's (~₹2,010/pack; x1 = ₹2,012,
  x2 = ₹4,020 incl 5% GST).

## Medybiz / KIRAN Patient Access Program (Keytruda PAP)

- **This correspondence lives on the google-ahfl account (ndr@ahfl.in), NOT google-draas.**
  All Medybiz/KIRAN emails go to/from ndr@ahfl.in. Always use service_name='google-ahfl'.
- **Ticket No: 7027** — the persistent thread ID for all Charitra Keytruda PAP communications.
  Thread started ~15-Jul-2026. Subject always: `RE : [Ticket No:7027] Infusion Confirmation Form and Prescription`.
- **Program contact:** kiranpapv3@medybizpharma.com (Thoyadakshi, Puja Kumari). Toll-free 1800 210 2983.
- **Infusion confirmation form:** Must be submitted within 48 hours of infusion.
  Submit to kiranpapv3@medybizpharma.com via reply-all on the ticket thread.
- **OTP for next cycle:** Generated only after the signed infusion confirmation form + prescription are validated.
  OTP required 72+ hours before next infusion date to avoid delays.
- **Email CC list (established pattern):** charitrakamath@gmail.com, rmurjani@gmail.com, anniekbaa@gmail.com, rnr@draas.com
- **Registered email for the PAP:** ndr@ahfl.in (not ndr@draas.com). All PAP correspondence uses ndr@ahfl.in as sending account.
- **SPS ID:** 1868282 (Charitra Murjani's patient ID in the KIRAN system).

### Infusion Confirmation Workflow

1. Patient receives Keytruda infusion at St John's (Dr Annie K Baa)
2. Fill the MSD Infusion Confirmation Form: patient name, SPS ID, cycle number, OTP (from email/SMS),
   vials received (typically 2), infusion date, patient signature, doctor signature
3. Scan the signed form (full image — no cutoff). If the scan is cutoff, Medybiz will reject and ask for re-submission.
4. Reply-all on the Ticket:7027 thread via **ndr@ahfl.in**, Cc the standard CC list, attach the full scanned PDF
5. Request OTP for next cycle delivery + confirm no delay to scheduled infusion date

### Scheduling pattern
- Infusions roughly every 3 weeks (21 days)
- July/August 2026 pattern: 12 Aug → 2 Sep (21-day cycle, Cycle 12→13)
- Prescription needed for each cycle, signed by Dr Annie K Baa

## Drive (ndr@draas.com)

- `Murjani Medical` folder: 1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V
- `Murjani Medical Invoices` subfolder: 1l4YOlo4HCxFAWkoVMMxT1JYloPUDq79R
- Index sheet **"Index of Charitra Medical Expepnse Invoices"** (keep mis-spelling):
  1g9aqYlZYcGbOZYWdeicT90cx55604e_3ZKYv0x0mf9w — tab Sheet1; header
  `Date of Invoice (MM/DD/YYYY) | Institute | Invoice Type | Amount | Reimbursed? | To be Claim | Additional Notes`;
  To-be-claim = `=if(NOT(E{r}),D{r},0)`; TOTAL row last with SUM formulas.
- Sample filed combo (2026-08-25): `20260825_Charitra_Murjani_Medicine_Invoices_202607-08_MythriPharma.pdf`
  → Drive id 1kEsSU6oMp3rj1lebzhdKr7rVGp0-zhH7; three Mythri invoices (06-Jul ₹2,012 · 22-Jul ₹4,020 ·
  10-Aug ₹4,020 = ₹10,052) appended as rows 24–26; totals extended to D28=sum(D2:D26), F28=sum(F2:F26)
  (₹6,55,462 / ₹4,03,677).

## Email-draft link patterns

### Star Health claim
- Draft to reimbursement.blr@starhealth.in, Cc Customer.NEFT@starhealth.biz + Charitra Kamath
- FROM = registered policy email (default: ndr@draas.com)
- Attach deskewed invoice PDF; ask whether OPD/medicine reimbursable or club with existing intimations

### Medybiz PAP infusion confirmation
- Reply-all on Ticket:7027 thread
- FROM = ndr@ahfl.in (google-ahfl account)
- To = kiranpapv3@medybizpharma.com
- Cc = charitrakamath@gmail.com, rmurjani@gmail.com, anniekbaa@gmail.com, rnr@draas.com
- Attach the signed infusion confirmation form PDF
- Build via raw Gmail API (MIMEMultipart/mixed with MIMEBase attachment) — gws_skill_bridge doesn't support attachments
- Set In-Reply-To + References to the Kiran email's Message-ID for proper threading