# RERA Model Form of Allotment Letter — Key Terms & Cancellation Rules

**Source:** RERA Model Form of Allotment Letter (Annexure-1, as per Section 4(2)(g) of RERA 2016). Verified 2026-08-25 from the Ranka Amber allotment letter PDF (10-page proforma, all fill-in fields blank).

## When to use
- Drafting an allotment letter / booking-confirmation email for a DRA plot or apartment client
- Answering "what happens on cancellation" — buyer-initiated or promoter-initiated
- Building a cancellation-terms draft where the user wants commercial terms (e.g. "15 days for agreement + legal verification, else entire amount forfeited")

## Structure of the document
ANNEXURE-1 → MODEL FORM OF ALLOTMENT LETTER. Mandatory to issue when booking / advance > 10% of cost of plot/apartment/building is collected. Allotment letter must be uploaded with the RERA application.

## Buyer-initiated cancellation — Clause 9 deduction table

| Window (from allotment letter date) | Deduction |
|---|---|
| Within 15 days | Nil |
| 16–30 days | 1% of unit cost |
| 31–60 days | 1.5% |
| After 61 days | 2% |

- Balance refunded within **45 days** of cancellation
- If refund delayed beyond 45 days → **interest at SBI highest MCLR + 2%** from the 46th day until payment

## Promoter-initiated cancellation (failure to execute agreement) — Clause 12

1. Allottee has **2 months** from allotment letter to execute + register the Agreement for Sale (extendable by promoter)
2. If missed → promoter serves a **15-day notice** to execute the agreement
3. Still not complied → allotment cancelled; promoter forfeits **up to 2% of the unit cost** and refunds the balance within 45 days
4. Refund delay beyond 45 days → same SBI MCLR + 2% interest

## Other clauses worth carrying into drafts
- **Clause 13 (Validity):** cancellation terms after agreement registration are governed by the registered agreement — the allotment letter's cancellation provisions apply only pre-registration
- Payment instalment schedule typically referenced to the agreement for sale
- Statutory cap: forfeiture "not exceeding 2% of the cost of the unit" is the RERA ceiling

## ⚠️ User-dictated vs template terms (Bharat, 2026-08-25)
Bharat dictated stricter commercial terms for a Ranka Udaya client booking Plot No. 5: **15 days to complete the Agreement + legal verification; if the client doesn't return/complete within 15 days, the ENTIRE booking amount is forfeited.** This is far stricter than the RERA model form's 2% cap. When drafting, use the user's dictated wording but ALWAYS flag the discrepancy to the user (DRAAS preference: the user decides commercial terms; the agent's job is to surface the legal gap).

## Plot layout extraction (companion technique)
Client booking emails often need plot-specific details from the layout image: plot No., dimensions (L × B in m), area (sqm + sqft), facing, AVAILABLE/SOLD status. Extract with `vision_analyze` (OCR handles the table) and cross-check against Kelsa lead notes (project, plot options being considered, quoted price per sqft, committed timelines) before composing the draft.