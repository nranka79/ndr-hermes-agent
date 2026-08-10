# DRA Employee Offer Letter → Payment Instruction → WhatsApp (accounts flow)

Class of task: an employee's appointment/offer letter exists on Drive; NDR
wants a WhatsApp message (from accounts group) to Eshwari (accounts) directing
salary payment per the letter — CTC, start date, prorated period, TDS, bank
details kept on record. Example: Gowri Singh, Marketing & Content Head,
DRA Ranka Holdings, letter dated 2026-07-31.

## Workflow (verified in session)
1. **Find the offer letter on Drive** (google-draas service). Query:
   `name contains '<Firstname>'` or `name contains 'offer' and fullText
   contains '<name>'`. Naming convention:
   `YYYYMMDD_DRA_<Company>_<Name>_AppointmentLetter_<Role>`
   e.g. `20260731_DRA_RankaHoldings_GowriSingh_AppointmentLetter_MarketingContentHead`.
   Company on the letter matters: Gowri is on DRA **Ranka Holdings** rolls
   (PAN AARFD2916M), not DRA Realty — payment instructions must name the right
   entity.
2. **Extract the document text**: Google Docs API — paragraphs alone return
   empty; must walk `body.content` handling BOTH `paragraph` elements AND
   `table` → `tableRows` → `tableCells` → nested content. (Compensation table
   lives in a table.) Use the recursive walker.
3. **Pull the two facts NDR wants quoted**: monthly CTC (all-inclusive) and
   effective/start date. Watch for template typos — the Gowri letter read
   "effective 16th June 1 April 2026" (merged template dates); NDR confirmed
   start = 16 June 2026. Flag the discrepancy, proceed with the confirmed date.
4. **Draft the WhatsApp payment instruction** to Eshwari (accounts,
   +91 81230 28716): CTC per month, appointment effective date, payment period
   (e.g. 16 Jun – 31 Jul 2026 = part June + full July), "after applicable
   deductions (TDS, professional tax etc.)", bank details to keep on record.
5. **Bank details**: NDR supplies them separately ("I will be providing the
   bank details right after") — draft with placeholders first, then regenerate
   the link when they arrive. Do not invent them.
6. **Generate the wa.me link with the `whatsapp_link` tool** (MANDATORY — never
   hand-build wa.me URLs). Individual recipient → include phone
   (`+918123028716`). Pass the full message text UNMODIFIED; the tool handles
   encoding. Use platform='telegram' so the returned display_link is
   MarkdownV2-safe for chat.
7. Present as: short confirmation of the facts pulled (CTC, start date,
   discrepancy flagged), then the link with the full message visible.

## Pitfalls
- Don't guess the effective date from the letter alone if it has a template
  merge error — confirm with NDR (he anchored it via the payment period).
- CTC may be "all-inclusive" with a statutory-breakup note ("detailed breakup
  communicated separately by accounts") — quote the all-inclusive monthly
  figure, don't compute a breakup.
- Performance pay may be quarterly/prorated per the letter — the message to
  accounts should stay at CTC/month level; let accounts compute net.
- Keep bank details in the message but never type account/IFSC from memory —
  wait for NDR to provide them.
