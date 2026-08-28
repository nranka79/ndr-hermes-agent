# Work Order Creation from Email Thread

Create a formal Work Order (Google Doc) from email-sourced commercial terms, then share in the TMP Drive folder for review.

## Trigger

User says "create a work order" or "prepare a work order" based on email correspondence with a vendor.

## Workflow

### Phase 1 — Mine the email thread

1. Search Gmail for the relevant thread (vendor name, project name, subject keywords)
2. Read all messages in the thread to extract:
   - Parties involved (client company, vendor company, representative)
   - Project name and description
   - Scope of services (itemized)
   - Commercial terms (retainer, ad spend, success fee, unit pricing)
   - Payment terms (advance %, milestone-based payments)
   - Duration / minimum commitment
   - Any special instructions or conditions
3. Identify the "final offer letter" or the last email that captures the agreed terms

### Phase 2 — Confirm terms with user before drafting

Before drafting, clarify any gaps or ambiguities. Present a structured breakdown:
- Total value: retainer vs ad spend vs other
- Payment schedule: % advance now vs % later
- Duration: minimum commitment period
- Issuing entity: which company the work order is from

### Phase 3 — Create the Google Doc in TMP folder

1. Locate the **TMP Drive folder** — search email history for a Drive folder link containing "TMP"
2. Create a new Google Doc via Drive API with naming: `YYYYMMDD_Project_Vendor_WorkOrder_DRAFT`
3. Populate content via Docs API (delete existing content first, then insert)
4. Standard sections: PARTIES, PROJECT, SCOPE, COMMERCIAL TERMS, PAYMENT TERMS, TERM & DURATION, GENERAL TERMS

### Phase 4 — Share & notify

1. Grant editor access to user (ndr@draas.com)
2. Grant viewer access to relevant stakeholders
3. Share the document link via Telegram
4. User reviews and may ask for corrections
5. Once approved, user downloads as PDF (File → Download → PDF Document)

## Common Commercial Term Patterns (Nishant — Jun 2026)

### Digital Marketing / Retainer + Ad Spend
- Monthly retainer (e.g., ₹60,000) + monthly ad spend budget (e.g., ₹2,00,000)
- Total monthly commitment = retainer + ad spend (e.g., ₹2,60,000)
- Payment: 50% advance (retainer + 50% of ad spend), 50% balance within 15 days
- Success fee on conversions (e.g., 0.5% per conversion)
- Minimum commitment period (e.g., 3 months), renewable subject to review
- Additional unit pricing for work beyond scope (static creative ₹X, video ₹Y)

### Standard Service PO Pattern
- 50% advance payment, 50% on completion / milestone / within 15 days
- Total order value includes applicable taxes
- Payment trigger: proforma converted to tax invoice by vendor

## Correction Cycle Pattern (Voice → Draft → Correct → Final)

**The user typically corrects commercial terms in 1-3 rounds after seeing the first draft.** Expect this and build it into the workflow:

1. **First draft** — Use what you extracted from the email thread. Make reasonable assumptions about ambiguous terms.
2. **User corrects via voice** — Update the doc immediately. Do NOT re-confirm every point — only the specific values the user corrected.
3. **Second pass** — The user may refine further (e.g., "50% now, 50% in 15 days" vs "100% upfront"). Re-apply the full payment section.
4. **Use the Doc replacement pattern** — When updating: deleteContentRange first, then insertText. Never append.

### Common corrections from this pattern:
- User says "retainer + ad spend" but the email only mentioned retainer → ask about the ad spend budget separately
- User corrects advance % after seeing the first draft (e.g., 50% → 100% → 50/50 split)
- User may say one project name in voice (e.g., "Amber") but email thread says another (e.g., "Udaya") — trust the email record and confirm
- Payment trigger sequence: proforma invoice → convert to tax invoice → process against PO → 50% now, 50% later

## Pitfalls

- **Voice vs written record:** The user's voice may say a different project name than what's in the email thread. Always trust the email thread's written record and confirm with the user.
- **Commercial terms change mid-session:** Update the doc and re-confirm after each correction — don't assume the first version is final.
- **Docs API content replacement:** Always deleteContentRange first, then insertText. Inserting into a non-empty document appends, creating duplicates.
- **Corrections are iterative:** The user will refine commercial terms after seeing the draft. Don't aim for perfection on the first pass — aim for a reasonable first draft that the user can correct.
- **Payment terms need explicit confirmation:** Don't assume the PO's stated terms (e.g., "100% upfront") are the final word. The user may have a different arrangement (e.g., 50% advance + 50% in 15 days).
- **TMP folder ID:** If not found, ask the user for the Drive folder link directly. Known TMP folder ID (Jun 2026): `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`
