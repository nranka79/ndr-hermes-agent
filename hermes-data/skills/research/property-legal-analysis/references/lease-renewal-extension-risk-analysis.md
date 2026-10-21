# Lease Renewal / Extension-Risk Analysis (can the tenant stay past expiry?)

Worked example verified 2026-10-12: **Miller's Road office building (No. 70/3), ground-floor tenant
"India Chai" = M/s. Silver tip Foods Pvt Ltd**, lease deed executed 01-Dec-2018, 9-year term
**01/02/2019 → 31/01/2028**. DRA was taking the full building on turnkey on the assumption the
ground floor vacates (for parking/lobby); the question was whether the tenant has ANY contractual
right to extend against the owners' will. Answer: **no renewal right** — but one deposit-refund
holdover hook exists. Deliverable shape below is reusable for any "review this lease for
vacancy/extension risk" ask.

## Extract first (scanned deeds have no text layer)
1. `pymupdf` text check → pure scan ("Scanned by CamScanner" only) → tesseract at 200 dpi (psm 6) page-by-page; keep the text file.
2. Pull: parties (lessor + lessee INCLUDING the corporate entity behind the brand — the operating
   entity is often a company, not the brand name), demised premises (area, floor), term start/end,
   rent + escalation, lock-in, security deposit, subletting ban, use restriction, expiry behaviour.
3. **Deed dates beat dictation:** NDR said "end December 2027" — the deed says **31/01/2028**
   (~15 months from the review date, not ~14). Always quote the deed's own term.

## The extension-risk checklist
1. **Fixed-term clause wording.** `Clause 1 DURATION`: "...ending on 31/01/2028 and on the expiry
   of the said period, the Lessee shall hand over the actual vacant possession of the Demised
   Premises **without seeking further extension of time**." — express no-extension, landlord-favourable.
2. **Absence of renewal/ROFR machinery.** Scan EVERY clause for: option to renew, renewal on same
   terms, right of first refusal, mutual consent to extend, "extended period". The Miller's Road
   deed had NONE — the phrase "extended period of lease" appears only conditionally (vacate at the
   end of any extended period IF one were agreed). Document the absence explicitly; do not infer
   silence = right.
3. **The security-deposit holdover hook (the ONE genuine risk).** A clause like Clause 5.5: if the
   Lessor fails to refund the SD at expiry while the Lessee is ready to hand over, the Lessee may
   **continue in occupation rent-free until the SD + 18% p.a. is paid**. This is a self-help remedy
   for non-refund, NOT an extension — but it gives the tenant a lawful foothold if the refund isn't
   ready on day 1 of expiry. Mitigation: simultaneous possession handover + SD refund (after
   adjusting arrears, per the deed) + deed cancellation, all on the expiry date; never let the
   owner accept a single rupee of rent after expiry.
4. **s.116 Transfer of Property Act holding-over.** Tenancy is renewed by implication ONLY if the
   lessor accepts rent/assents after expiry. Owner instruction: refuse post-expiry rent; then any
   continued occupation is a tenancy at sufferance → ejectment under the TP Act.
5. **Rent Act exposure.** Karnataka Rent Act 1999 protects premises ≤ ₹3,500/mo rent in BBMP areas;
   a ₹1,00,000/mo lease is OUTSIDE it → no statutory tenancy shield, no eviction-proceedings
   complexity. General rule for Indian metros: check the state's rent-control exemption threshold
   BEFORE predicting eviction difficulty.
6. **Subletting as an early-exit lever.** Clause 6 (no sublet/assign/parting-with-possession without
   written consent) — verify who PHYSICALLY operates the outlet. Brand ≠ tenant entity; if a
   different entity operates (franchise/SPV), that is a breach → termination route BEFORE expiry.
7. **Termination clauses.** Usually: expires by effluxion of time (Clause 20.1) + default route
   (rent 2 consecutive months unpaid → 15-day rectification notice → termination, subject to SD
   refund). Note whether early determination needs tenant notice (2 months here) — natural expiry
   needs none.

## Action-plan output (what NDR expects)
- Written "no extension, possession due <deed expiry date>" notice ~3–6 months before expiry.
- SD refund ready simultaneously with possession; deed cancellation per the refund clause.
- Owner must refuse post-expiry rent (else s.116 renewal).
- Verify the operating entity vs the named lessee (subletting check).
- State the corrected expiry date prominently — NDR's recollection is frequently off by a month.

## File handling
Rename per DRA convention using the DEED's execution date (P14): `20181201_MillersRoad70-3_LeaseDeed_SilvertipFoodsPvtLtd.pdf` → filed under the project's **Title** folder (DRA Realty → Millers Road Office Building → Title), not TMP, not Legal Notices.