# Charitra Murjani Medical Communication Context

## ⚠️ Two Separate Account Contexts

Charitra's care involves **two independent communication channels** on different accounts:

| Context | Account | Vault | What it's for |
|---|---|---|---|
| **Medical/Doctor comms** | ndr@draas.com | google-draas | Treatment discussion, PET scans, drug queries with Dr. Sameer/Dr. Annie |
| **KIRAN PAP logistics** | ndr@ahfl.in | google-ahfl | Infusion confirmations, prescriptions, Medybiz pharmacy coordination |

Treat them as separate — do NOT cross accounts. A drug-alternative query belongs on draas.com; a cycle-12 infusion confirmation belongs on ahfl.in.

---

## Context A: Medical/Doctor Communications (ndr@draas.com)

### Account
- **Account**: ndr@draas.com (google-draas vault)
- DO NOT use ahfl for doctor queries

### Doctors
| Person | Email |
|---|---|
| Dr. Sameer Rastogi | samdoc_mamc@yahoo.com (NOT dr.sameer.rastogi@gmail.com) |
| Dr. Annie (Annie Baa) | anniekbaa@gmail.com (NOT anniejames555@gmail.com) |

### Patient / Family
| Person | Email | Notes |
|---|---|---|
| Charitra Murjani (Chinky) | **charitrakamath@gmail.com** ← ACTIVE | `murjanicharitra@gmail.com` is OBSOLETE — NDR confirmed wrong Aug 2026. Thread consistently uses charitrakamath@gmail.com. |
| Roshni Ranka | **rnr@draas.com** | `rmurjani@gmail.com` is older/obsolete |

### Active Thread
- **Subject**: "Re: Post-Chemo PET-CT Scan (Ms. Charitra Murjani) and Guidance on Maintenance"
- **Thread ID**: 19b21cfeb1c6b4a7 (on google-draas)
- **Started**: Dec 2025, ongoing Aug 2026

### Current Treatment (Aug 2026)
- Pembrolizumab (Keytruda) immunotherapy + Axitinib 10 mg daily
- Known Axitinib brands: Axinix 5mg (Cipla), **Glenmark AXZYB 5 mg** (sourced Aug 2026 when Axinix was out of stock)
- PET shows stable disease; mass near airway/food pipe

### Drug-Out-of-Stock Email Pattern
When Axitinib (or similar) is unavailable at Nishant's 3 pharmacies:
1. Find thread on ndr@draas.com (google-draas vault, NOT ahfl)
2. Confirm drug name + dose from thread body
3. Verify recipient emails from thread headers (never guess)
4. Reply to latest message with proper threading (In-Reply-To + References)
5. Body: state drug + dose + brand, stock running out, ask for alternative generic
6. CC charitra (**charitrakamath@gmail.com** — NOT murjanicharitra@gmail.com) + Roshni (rnr@draas.com)
7. Create as DRAFT only; verify in Drafts folder after creation

---

## Context B: KIRAN PAP Logistics (ndr@ahfl.in)

### Account
- **Account**: ndr@ahfl.in (google-ahfl vault)
- DO NOT use draas.com for PAP logistics — the thread does not exist there

### What This Channel Is For
Every 2-3 weeks, NDR submits **Infusion Confirmation Form** (signed by Dr. Annie) + **Prescription** (next scheduled infusion date) to the KIRAN Patient Access Program (MSD/Medybiz) so they release the next cycle's free vials of Keytruda.

### Key Participants
| Person | Role | Email |
|---|---|---|
| **Kiran PAP Team** | Program coordinators (Medybiz) | **kiranpapv3@medybizpharma.com** (To) |
| **Charitra Murjani** | Patient | **charitrakamath@gmail.com** (Cc) — verify from thread headers each time |
| **Roshni Ranka** | Family | **rnr@draas.com** (Cc) |
| **Dr. Annie K. Baa** | Prescribing oncologist | **anniekbaa@gmail.com** (NOT on email CC — signs the infusion form) |

### Active Thread — KIRAN PAP
- **Subject**: `RE : [Ticket No:7027] Infusion Confirmation Form and Prescription`
- **Thread ID**: 19f657773f75c067 (on google-ahfl)
- **Started**: Jul 2026, ongoing with every cycle
- **Submission email**: kiranpapv3@medybizpharma.com
- **Patient SPS ID**: 1868282 (must be on the infusion confirmation form)

### Document Types & Naming Convention
Files go into the **Murjani Medical** folder on Drive (folder id: 1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V).

**Naming pattern observed from existing files:**
```
YYYYMMDD Charitra [Document Type] [Details].pdf
```
Examples:
- `20260722 Charitra Keytruda Infusion Confirmation MSD.pdf` — the signed infusion confirmation form
- `20260722 Charitra Pembrolizumab Prescription St Johns.pdf` — the signed prescription
- `20260803_Charitra_ChinaClinicalTrials_Research_v1.0.html` (research, not submitted to PAP)
- `20260722 Charitra Cough Prescription St Johns DrAnnie.pdf` (ancillary prescriptions)

**Each cycle creates 2 documents to submit:**
1. **Infusion Confirmation Form** — signed by patient rep + Dr. Annie, showing cycle number, vials infused, infusion date
2. **Prescription** — showing Inj. Pembrolizumab 200 mg, next scheduled infusion date

### Submission Workflow (per cycle)
1. **Receive documents** — NDR sends scanned PDFs of the signed infusion form + prescription (may be scanned images)
2. **OCR/extract** — if scanned (0 text layer), use pymupdf to render at 150 DPI then `vision_analyze` to read all text
3. **Name the files** per convention: `YYYYMMDD Charitra Keytruda Infusion Confirmation MSD.pdf` and `YYYYMMDD Charitra Pembrolizumab Prescription St Johns.pdf`
4. **Upload to Drive** — into `Murjani Medical` folder
5. **Find the thread** — on google-ahfl, search `q='kiranpapv3 subject:Infusion Confirmation'`
6. **Compose email reply** — Reply-all in the existing thread:
   - **To**: kiranpapv3@medybizpharma.com
   - **Cc**: charitrakamath@gmail.com, rnr@draas.com, anniekbaa@gmail.com
7. **Draft body pattern** (from Aug 3 email):
   - State: sharing Infusion Confirmation Form (signed) for Ms. Charitra Murjani (SPS ID: 1868282) and the prescription for the next scheduled infusion
   - Ask them to ensure Keytruda under KIRAN PAP is available on the scheduled infusion date (from the prescription)
   - Ask them to confirm the prescription's doctor/hospital details are in order — because a prior cycle had issues
   - Request confirmation by the next day to avoid last-minute surprises
8. **Attach** the two PDFs from Drive
9. **Create as DRAFT only** — verify in Drafts folder, report to user

### Pitfalls
- **Email address verification**: Charitra has multiple emails on record (`charitrakamath@gmail.com`, `charitra_murjani@yahoo.com`, `Charitramurjani77@yahoo.com`, `murjanicharitra@gmail.com`). The ACTIVE one used on ALL thread cycles is **charitrakamath@gmail.com**. Always verify from the LATEST thread message's Cc/To headers before drafting — do NOT use any other address.
- **Dr. Annie is NOT on the email CC** — she signs the documents but is not a thread participant. NDR may explicitly ask to add her (anniekbaa@gmail.com).
- **Roshni Murjani (rmurjani@gmail.com, Charitra's sister)** is distinct from Roshni Ranka (rnr@draas.com, NDR's wife). Roshni Murjani was CC'd on earlier threads (Feb 2026) but recent cycles use rnr@draas.com instead. Verify from the latest thread to avoid dead addresses.
- **Scanned PDFs have 0 text layer** — use pymupdf render at 150 DPI → `/tmp/...png` → `vision_analyze`. Do NOT expect pdftotext to work. 300 DPI can OOM the VPS; 150 DPI is safe.
- **OTP-based delivery** — Medybiz releases vials by OTP; the thread shows this is the normal process. The email should ask them to confirm availability before the infusion date rather than assume auto-delivery.
- **The thread lives on ndr@ahfl.in** — build_service('gmail','v1',service_name='google-ahfl'). Default gmail tools route to google-draas and will not find these messages.

---

## Pitfall — Multiple email addresses per person (cross-context)
All known addresses for a person across BOTH contexts are listed, but NOT all are active. Check the LATEST thread message's headers for the correct address — not the full list. When NDR sent to `murjanicharitra@gmail.com` (one of Charitra's old addresses), he confirmed it was wrong. The active address for Charitra on both threads is `charitrakamath@gmail.com`.