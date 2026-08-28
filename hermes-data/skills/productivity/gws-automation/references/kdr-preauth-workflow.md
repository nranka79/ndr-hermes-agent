# KDR Pre-Op + Insurance Pre-Authorization Workflow

The recurring pre-surgery workflow for Kanta D. Ranka (KDR, KDR Medical folder `0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s`). Distinct from the post-claim `insurance-claim-escalation` skill — this covers the **cashless pre-authorization request** before a planned surgery, plus the family-accounts reconciliation that happens in parallel.

## Trigger
- Nishant says "mom's surgery is on Wednesday", "KDR needs pre-auth", or similar
- 5+ medical PDFs land in `/data/hermes/document_cache/` over 1-3 days
- The workflow combines: filing + accounts WhatsApp + insurance coordinator draft email

## The 3-Deliverable Pattern

Every pre-op cycle produces **three artifacts**:

1. **Files filed in Drive** — reports in `KDR Medical/` root, invoices/receipts in `KDR Medical/Invoices/`. Naming convention `YYYYMMDD_Hospital_Description.pdf`.
2. **WhatsApp statement for family accounts group** — confirms which payments were made, what's been filed, what's still missing. Sent to the family group (NOT to insurance — this is internal).
3. **Gmail draft to insurance coordinator** — formal pre-authorization request with selected reports attached. Held as a draft until the coordinator's email is available.

## Step 1 — Classify & Dedup BEFORE Filing

User instruction, repeated in voice notes: *"if there are duplicates, please ignore the duplicates, if there are already filed versions of it, please ignore the duplicates"*. Always dedup before uploading.

**Procedure:**
1. Read every new PDF (Adobe Scans especially — they may be re-scans of docs already on Drive)
2. For each, classify as: **report** (root), **receipt/invoice** (Invoices/), or **duplicate (skip)**
3. To detect duplicates: search Drive for the same document by distinctive text (e.g. "Bill No MHM260CS047124", "OPB12630833", doctor name + date)
4. Skip upload for confirmed duplicates; report them to the user as "already filed, ignored"

Common Manipal/Trustwell patterns to expect:
- Re-scans of the same receipt sent in multiple WhatsApp forwards
- Lab reports sent page-by-page ("Lab Report-1", "Lab Report-2"...)
- OPD notes for the same doctor on the **same day** (these are usually duplicates of one physical note — confirm before assuming)

## Step 2 — File With the YYYYMMDD Convention

Use this naming skeleton for KDR medical files (Kanta Ranka):

| Type | Folder | Pattern |
|------|--------|---------|
| OPD note | `KDR Medical/` root | `YYYYMMDD_Hospital_KantaRanka_OPDNotes_DrName.pdf` |
| Lab report | `KDR Medical/` root | `YYYYMMDD_Hospital_KantaRanka_LabReport_Test_Partial_or_Final.pdf` |
| Radiology | `KDR Medical/` root | `YYYYMMDD_HDR_ExamType_Hospital.pdf` |
| Other test | `KDR Medical/` root | `YYYYMMDD_HDR_TestName_Hospital.pdf` |
| Receipt / bill | `KDR Medical/Invoices/` | `YYYYMMDD_Hospital_KantaRanka_Receipt_Description_Amount.pdf` |

For partial lab reports (only some tests back), include a status suffix:
- `20260711_..._LabReport_DDimer_Partial_ANA-CCP-ANCA-Pending.pdf`

For multiple OPD notes the same day (rare but happens — initial consult + review with reports), use a descriptor:
- `20260710_..._OPDNotes_DrKasargod.pdf` (initial, 16:26 PM)
- `20260711_..._OPDNotes_DrKasargod_ReviewVisit_MildRiskDisclosure.pdf` (review at 12:45 PM, with risk note + plan)

**Pitfall:** Do NOT assume a later-dated document supersedes an earlier one. Each clinical encounter is distinct — file both. In the KDR 10/07 vs 11/07 Kasargod OPD notes case, the 10/07 note ordered the workup, the 11/07 note reviewed the results + documented the risk disclosure. Both are needed; they're different clinical events.

## Step 3 — WhatsApp Statement for Family Accounts Group

The family accounts group is internal. The message is a **reconciliation confirmation** — "here's what I paid, please pass the necessary accounting entries."

**Structure (in this exact order — this is the user's preferred format):**
1. Greeting + scope statement (patient name, UHID, date range, Trustwell/Manipal UHIDs)
2. Numbered list of each payment: date, place, description, bill/receipt numbers, amount
3. Total on file
4. "FOR CONTEXT (NO RECEIPTS)" — items where the consultation was billed under insurance / hospital billing, no separate receipt
5. "TO FOLLOW" — receipts Nishant is still chasing
6. Signature

**Length:** ~2,000 chars. Always well under wa.me URL limit (8,192).

**Key fields to include per payment:**
- Date
- Hospital / location
- Doctor(s) involved
- Itemized services (the bill line items, not just the total)
- Bill number AND receipt number (when shown)
- Amount
- Payment mode (Axis Bank, UPI, Visa card last 4)

**For "STILL TO RECEIVE" lines:** if a service was actually rendered but no receipt issued (e.g. consultant visits billed under insurance), use the "FOR CONTEXT — NO RECEIPTS" line instead of "STILL TO RECEIVE". The user will explicitly correct you on this — see KDR Kasargod/Sunil Dwivedi case, Jul 2026.

**Number format pitfall — Indian numbering convention:**
- `1,50,00,000` = **₹1.5 Crore** (NOT ₹15 lakhs)
- `2,00,000` = **₹2 Lakh** (NOT ₹200 thousand)
- `2,10,00,000` = **₹2.1 Crore** (₹2 Crore 10 Lakh)
- The lakh/crore separators are NON-OBVIOUS — `1,50,00,000` has two 50s, but the second 50 is ten-thousands, not another fifty-thousand.
- **Always re-derive**: strip commas, count digits from the right (rightmost 3 = thousands, then groups of 2 = lakhs, then 1 group of 2+ = crores)
- See `references/indian-numbering-convention.md` for the full conversion table

## Step 4 — Gmail Draft to Insurance Coordinator

The insurance coordinator at the hospital (e.g. Charan at Trustwell, 2026) handles cashless pre-auth. They're introduced by the surgeon's operations coordinator (Sridhar).

**Setup:**
- Get coordinator's mobile via wa.me (preferred) or voice
- **Don't ask for coordinator's email until just before sending** — they may take 1-2 days to share
- Create the draft in Gmail with NO `To:` header (Gmail rejects placeholder emails with `"Invalid To header"`)
- Use a custom `X-Pending-To:` header in the MIME for your own tracking
- Leave the recipient field blank in Gmail UI for the user to fill in

**Draft content sections (use this exact order):**
1. Greeting + Sridhar referral
2. PATIENT block (name, UHID, age/gender, mobile, surgery date)
3. PROCEDURE block (operation name, anaesthesia, surgeon, anaesthetist, hospital)
4. INSURANCE block (insurer, plan, active policy number, base SI, cumulative bonus, total available SI, premium, TPA)
5. PRIOR SURGERY block (if any, brief — 1 line)
6. ATTACHED list (5-7 reports, each with 1-line description and date)
7. "ADDITIONAL WORKUP PERFORMED BUT NOT ATTACHED" list (on request)
8. REQUEST block (4 numbered asks: doc list, ETA, reimbursement process for OP tests, day-of-surgery contact)
9. Closing + signature

**Insurance block — get the policy data right:**
- Always pull the **active** policy from the most recent renewal notice email
- For Royal Sundaram Lifeline Elite, the policy schedule lists:
  - Base Sum Insured (e.g. ₹1,50,00,000)
  - Cumulative Bonus (e.g. ₹1,20,00,000)
  - Total Available Sum Insured = base + CB (e.g. ₹2,70,00,000)
  - Annual premium (e.g. ₹2,09,731)
- **Do NOT confuse the renewal advice (sent before payment) with the renewal receipt (sent after payment)** — they may have different policy numbers (LLA0016946000106 vs LLA0016946000107 in KDR's case)
- If the user has confirmed renewal, use the new policy number; drop the "please confirm active policy number" request

**Attachment selection — the user is opinionated:**
- The user will explicitly say which reports to attach and which to exclude
- Common exclusions: cardiologist clearance (when pulmonologist is the relevant specialist for the surgery)
- Common inclusions: surgeon's consultation/advice, audiological evaluation (for ENT), anaesthesia eval, bloods, pulmonology clearance
- If unsure, ask. Don't attach extra reports without permission.

**MIME construction pattern** (Python + `email.mime.*`, not Google Docs API):
```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import base64

msg = MIMEMultipart('mixed')
msg['From'] = 'ndr@draas.com'  # or ndr@ahfl.in
# NO msg['To'] — Gmail rejects drafts with placeholder addresses
msg['X-Pending-To'] = 'recipient@pending (waiting for them to share)'
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))

for fid, fname in attachments:
    media = drive.files().get_media(fileId=fid)
    data = media.execute()  # bytes
    part = MIMEApplication(data, Name=fname)
    part['Content-Disposition'] = f'attachment; filename="{fname}"'
    msg.attach(part)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}
).execute()
```

**Why this pattern:** Gmail API `drafts.create()` with `message.raw` accepts a fully-formed MIME document including attachments. The native `gmail.users().messages().send()` won't accept a `To:` header that's a placeholder string — it'll return 400 `"Invalid To header"`. Leaving `To:` out lets the user add it in the Gmail UI.

## Step 5 — Cross-Stuff: Update the DRAAS Contacts Sheet

The insurance coordinator and ops coordinator are **new contacts** for KDR's record. Add to both Google Contacts (People API) AND the NDR DRAAS contacts sheet.

**DRAAS sheet column layout (90+ columns — pad row to header length):**
The header has ~93 columns. Append the full row, the API handles the truncation. Critical columns:
- col 1 (A): First Name
- col 7 (G): Name Prefix
- col 10 (J): File As
- col 11 (K): Organization (e.g. "Trustwell Hospital")
- col 12 (L): Organization Title
- col 13 (M): Department
- col 15 (O): Notes (context)
- col 17 (Q): Labels (e.g. `* myContacts`)
- col 27 (AA): Phone 1 - Label
- col 28 (AB): Phone 1 - Value
- col 93+: misc dates

**Pitfall:** If the new contact's name + phone already exists in the sheet, **update the existing row** rather than appending. Append creates duplicates. KDR's case: Charan was already in the sheet at row 717 with just first name + mobile.

**`+91 9845252011` in Sheets:** A leading `+` makes Google Sheets interpret the cell as a formula and render `#ERROR!`. Use `valueInputOption='RAW'` for the values().update() call.

## Step 6 — The "Patient is Cleared" Risk Disclosure Note

The pulmonologist's clearance note (or surgeon's, or anaesthetist's) often contains a **risk disclosure** that's important to capture in the file. Examples from KDR Jul 2026:
- Dr. Kasargod: "PATIENT HAS MILD RISK FROM PULMONOLOGY SIDE FOR PERIOPERATIVE COMPLICATIONS LIKE LONG TERM VENTILATION / PULMONARY INFECTIONS ETC DURING/ AFTER SURGERY UNDER GENERAL ANAESTHESIA. THIS HAS BEEN EXPLAINED IN DETAIL TO THE PATIENT AND ATTENDERS."

**This risk disclosure matters for the Charan pre-auth file** because the insurance coordinator will note the elevated risk when authorising. Make sure this note is filed separately and (if the user approves) attached to the draft.

## Reference Workflow Template

When the user signals a new pre-op cycle (e.g. "mom's getting her knee replaced in October"), the first move is to:

1. Create a folder check — confirm KDR Medical + Invoices still exist
2. Get the surgery date + surgeon + hospital from the user
3. Wait for the pre-op workup to be done (tests, consults, op notes)
4. Trigger this workflow as files land

If surgery is more than 2 weeks out, the cycle is short. If less than 1 week, accelerate — files will land daily, the WhatsApp statement may need updating, the Gmail draft needs to be ready before the coordinator's email arrives.
