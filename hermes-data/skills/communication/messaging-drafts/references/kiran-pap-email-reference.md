# Kiran PAP — Infusion Email Reference

## Program Identity
- **Name:** Kiran Patient Assistance Program (Kiran PAP)
- **Email:** kiranpapv3@medybizpharma.com
- **Context:** Free Keytruda (pembrolizumab) supply for Ms. Charitra Murjani under the Kiran PAP
- **Medication:** Pembrolizumab (Keytruda) — immunotherapy, infused at St. John's Medical College Hospital, Bengaluru
- **Patient:** Ms. Charitra Murjani — on continuous treatment cycle for ASPS (Alveolar Soft Part Sarcoma)

## Email Pattern (used for every infusion notification)
Subject: `Re: Infusion Confirmation`

Standard body structure:
1. Reference last infusion date and confirm it was administered
2. List attached documents (Infusion Confirmation Summary + Prescription)
3. State next infusion date
4. Request OTP and delivery confirmation
5. Reference Kiran Patient Assistance Program

## Escalation / Complaint Pattern (NEW — Jul 2026)

**Trigger:** Prescription was sent but rejected without通知, only discovered after proactive follow-up.

**Tone:** Polite, cooperative but firm/strong — NOT aggressive but clearly expresses disappointment at lack of communication.

**Subject:** `Re: Infusion Confirmation – Charitra Murjani – Updated Prescription Attached`

**Key structural elements:**
1. State what was sent (prescription on 19 Jun via email)
2. State what wasn't received (no OTP, no delivery confirmation, no rejection notice)
3. State how it was discovered (only after user proactively called on the morning of infusion day)
4. Express surprise / disappointment — "surprised and disappointed", "could have been sorted out"
5. Emphasize patient context — continuous treatment cycle, critical care, legitimate patient at St. John's
6. Attach the corrected/cleaner prescription
7. Request immediate processing and delivery today
8. No threats — just firm request for cooperation

**CC pattern:** `rnr@draas.com` (Roshni — handles the coordination), `charitrakamath@gmail.com`

**From:** `ndr@ahfl.in`

## Timeline of Events (Updated Jul 2026)

| Date | Action | By | Notes |
|------|--------|----|-------|
| 25 Mar 2026 | First infusion scheduling email | Charitra Kamath | Initial contact |
| 27 Feb 2026 | Infusion Confirmation Summary | Charitra Kamath | Post-infusion form |
| 5 Feb 2026 | Infusion confirmation | Charitra Kamath | Post-infusion form |
| 17 Mar 2026 | Prescription sent (drahomes.in) | Nishant | "supersede earlier email" for 18 Mar infusion |
| 27 Apr 2026 | Infusion confirmation (draas.com) | Nishant | Next infusion 29 Apr; OTP request |
| 20 May 2026 | Infusion confirmation (ahfl.in) | Nishant | Next infusion 20 May; OTP + free vials request |
| **19 Jun 2026** | **Prescription sent via ahfl.in** | **Nishant** | **Prescription for next infusion cycle** |
| **1 Jul 2026** | **Morning reminder email sent** | **Nishant/Roshni** | **No OTP/delivery confirmation received** |
| **1 Jul 2026** | **Roshni called Kiran PAP directly** | **Roshni (rnr@draas.com)** | **Discovered rejection — prescription name illegible** |
| **1 Jul 2026** | **Clean prescription rescanned & sent** | **This session** | **New cleaner version with visible name** |

## Prescription Handling Pattern

**Problem:** Kiran PAP rejected a previous prescription because the patient's name was not visible on the scanned document. They did not communicate this — went silent until the user called on infusion day.

**Fix pattern:**
1. Rescan the prescription ensuring ALL text (especially patient name) is clearly visible
2. Upload to Drive → Murjani Medical folder with naming convention: `20260701 Charitra Pembrolizumab Prescription St Johns.pdf`
3. Attach to escalation email with note that this is a "cleaner, fully legible scanned version"

**Naming convention:** `YYYYMMDD Charitra [Procedure] [Source].pdf`
- E.g. `20260701 Charitra Pembrolizumab Prescription St Johns.pdf`
- Stored in Drive folder: `Murjani Medical` (ID: `1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V`)

## Reply Chain Resolution

When asked to "reply to the previous email chain about infusion confirmation":
1. **Search** `infusion confirmation` in Gmail — returns ~200 results
2. **Filter** by `from:ndr@draas.com` and `to:kiranpapv3@medybizpharma.com` — narrows to outbound thread
3. **Identify most recent sent email** — `19dce3194b57d174` (27 Apr 2026, next infusion 29 Apr 2026)
4. **Note:** Emails sent from `ndr@ahfl.in` will NOT appear in `ndr@draas.com` inbox unless forwarded. Check for forwarded copies or ask user for ahfl.in auth.
5. **Extract** `In-Reply-To` and `References` headers from that message for threading
6. **Draft FROM address** = `ndr@ahfl.in` (NOT `ndr@draas.com` or `ndr@drahomes.in`) — user-specified
7. **Draft TO** = `kiranpapv3@medybizpharma.com`; **CC** = `rnr@draas.com, charitrakamath@gmail.com`
8. **Draft body structure**: depends on intent — standard infusion notification OR escalation/complaint
9. **Send draft for user review before sending** — user explicitly reviews all drafts

## Draft Delivery Limitation

The Hermes Gmail OAuth is for `ndr@draas.com`, not `ndr@ahfl.in`. Drafts cannot be directly created in the ahfl.in account without separate authorization. 

**Workflow when user says "put it in my ahfl box":**
1. Generate a fresh auth URL for `ndr@ahfl.in` (modify login_hint)
2. Present it to the user: click to authorize → I'll save the draft directly
3. If user prefers not to authorize, present the full draft text + Drive link to the prescription so they can compose manually

When drafting a new Kiran PAP email:
1. Determine if it's a standard infusion notification or an escalation/complaint
2. Replicate the appropriate pattern
3. If user authorizes ahfl.in, save as Gmail Draft; otherwise present text for manual use
