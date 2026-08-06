# Trustwell Hospital / Kanta Ranka (KDR) — pre-authorisation playbook

Source of truth for any follow-up to the right stapedectomy admission
scheduled Wed 15 Jul 2026 at Trustwell Hospital, J.C. Road, Bengaluru.
Captured from the live session 14 Jul 2026 (NDR) so that the next
session can pick up without re-discovering the same context.

## Patient & clinical

- **Patient:** Mrs. Kanta D. Ranka (KDR), UHID **TWH-74537**
- **Procedure:** Right stapedectomy / stapedotomy
- **Surgeon:** Dr. Deepak V. Haldipur, Consultant ENT Specialist,
  Trustwell Hospital (ENT Department)
- **Anaesthesia pre-op:** Dr. N.S. Chandra Shekara, Trustwell
- **Pulmonology workup:** Dr. Vasunethra Kasargod, Manipal Hospital
  Millers Road (10–11 Jul 2026)
- **Admission date:** Wednesday, **15 July 2026**

## Contacts (canonical, verified against Google Contacts)

| Person              | Role                                       | Phone           | Notes                                                                                     |
|---------------------|--------------------------------------------|-----------------|-------------------------------------------------------------------------------------------|
| **Sridhar**         | Operations Coordinator — Dr. Haldipur (ENT)| +91 94497 84569 | Trustwell Hospital, ENT / Audiology Operations. Search "Sridhar" in People API — only first name stored. |
| **Charan**          | Insurance Coordinator, Trustwell           | +91 98452 52011 | Referred by Sridhar. Pre-auth / cashless for KDR. Trustwell Hospital Insurance Coordinator. |
| **Dr. Deepak Haldipur** | Surgeon (office)                        | +91 80 45666789 / 45666851 | customercare@trustwellhospitals.com                                                          |
| **Elumali**         | Trustwell, alternate Dr. Haldipur contact  | +91 99020 12550 | Likely a different coordinator — keep on file, but Sridhar is the primary ops contact.     |
| NDR                 | Son & primary caregiver                    | +91 98800 55634 | Use as the "from" number in outbound WhatsApp messages.                                     |

## Insurance — Royal Sundaram Lifeline Elite (active)

- **Insurer:** Royal Sundaram General Insurance Co. Ltd
- **TPA:** Medi Assist Insurance TPA Pvt. Ltd
- **Plan:** Lifeline Elite (Health)
- **Policy number:** **LLA0016946000107**
- **Period:** 14/06/2026 → 13/06/2027 (FY 2026-27, renewal confirmed)
- **Base Sum Insured:** Rs 1.5 Cr
- **Cumulative Bonus:** Rs 1.2 Cr
- **Total Available:** Rs 2.7 Cr
- **Source of policy PDF:**
  - **Kelsa** — DRA account, **Policies pipeline**, record for
    Kanta Ranka, attachment field `policy` → S3 URL (the
    authoritative source per the user).
  - **Google Drive backup** (in case Kelsa is unreachable):
    `RoyalSundaram-Lifeline-Elite_kanta-ranka_LLA0016946000107_2026-06.pdf`,
    Drive file id `1OHJgUrl2-uYIqXzhNAnYil4uHCOeIYYZ`, modified
    13 Jul 2026, 484 KB.
  - **Gmail original:** Royal Sundaram renewal notice
    `RoyalSundaramVconnect@royalsundaram.in`, 30 Mar 2026, attached
    `LLA0016946000107.pdf` (262 KB).

## Documents already on file (sent 12 Jul 2026 to insurance@trustwellhospitals.com)

1. Dr. Haldipur — Consultation / Advice & admission recommendation (09/07/2026)
2. Audiological evaluation — PTA + Impedance (09/07/2026)
3. Anaesthesia pre-op evaluation — Dr. Chandra Shekara (10/07/2026)
4. Pre-op bloods (10/07/2026)
5. Pulmonology OPD note — Dr. Kasargod, initial consult (10/07/2026, Manipal)
6. Pulmonology OPD note — Dr. Kasargod, review with CTPA / PFT / D-Dimer
   results, mild-risk disclosure for GA (11/07/2026, Manipal)

**Additional workup available on request (not yet sent):**
2D Echo, ECG, Chest X-Ray (09/07/2026, Trustwell), CTPA (11/07/2026,
Manipal), PFT, D-Dimer, ANA / Anti-CCP / ANCA panel (in progress).

## Two-message playbook (already drafted 14 Jul 2026)

### Sridhar — operations coordinator

WhatsApp, +91 9449784569, message asks for:
1. Reporting time + which entrance / floor / counter
2. Confirmation that all 6 attachments + active policy LLA0016946000107
   are on file
3. Acknowledge that Charan is being looped in for cashless pre-approval
4. List of registration / check-in formalities + offer to send someone
   from NDR's office today itself to complete paperwork in advance

### Charan — insurance coordinator

WhatsApp, +91 98452 52011, message:
1. Attaches the policy PDF (Royal Sundaram Lifeline Elite,
   LLA0016946000107) and asks for pre-authorisation status confirm
2. Asks which pre-op workup items are covered under the cashless
   pre-auth pathway, and for any items not covered, the reimbursement
   route (documents, submission timeline, Royal Sundaram direct vs
   Medi Assist)
3. Notes that Sridhar is being asked to align with Charan on the
   pre-approval so it's in place today

**Attachment caveat:** wa.me deep links cannot carry file
attachments — Charan needs to attach the policy PDF in WhatsApp
himself after the chat opens, OR receive the policy via a separate
Gmail draft with the PDF attached (preferred for the policy itself).

## Reimbursement route — known unknowns (flag for Charan)

- Whether pre-op OPD workup at Manipal Millers Road (Dr. Kasargod,
  10–11 Jul) is automatically covered under the cashless pre-auth
  pathway, or whether each item is reimbursed separately.
- Submission timeline and channel: Royal Sundaram direct vs. via
  Medi Assist TPA.
- Documents typically required: original bills, payment receipts,
  investigation reports, treating-doctor's certificate, discharge
  summary, claim form, photo ID, policy copy.

## Open follow-ups (next session should track)

- [ ] Sridhar: confirm reporting time, formalities, whether someone
      from NDR's office should be sent today.
- [ ] Charan: confirm pre-approval issued; confirm reimbursement
      route for Manipal Millers Road pre-op workup.
- [ ] Kelsa DRA Policies pipeline — Kanta Ranka record, the `policy`
      attachment field. Verify S3 link is reachable; if not, share the
      Drive backup URL with Charan as fallback.
- [ ] If the user has not sent the policy PDF via WhatsApp, draft a
      Gmail draft to Charan with the PDF attached from
      ndr@draas.com (DRAFT only — never send per Hermes policy).
