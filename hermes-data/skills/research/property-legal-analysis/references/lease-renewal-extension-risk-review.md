# Lease Renewal / Extension Risk Review — "can the tenant stay when the landlord wants them out?"

Class: incoming lessee / buyer of a building asks — the ground-floor tenant's lease ends soon; can the tenant force an extension and block our possession plan (parking/lobby redevelopment)?

Validated 2026-10-12: Silver tip Foods Pvt Ltd (India Chai outlet) lease at No. 70/3 Millers Road, Bangalore. Owners = M. Akber Hussain family (all via GPA holder); 9-yr lease 01/02/2019–31/01/2028, 2,675 sq ft GF + 1 car park, ₹1L/mo rent + 5% p.a., SD ₹6L.

## Workflow
1. OCR the deed if scanned (CamScanner PDFs have no text layer; pymupdf `page.get_text()` returns only "Scanned by CamScanner"). Render at 200 dpi + `tesseract --psm 6 -l eng` per page.
2. Extract: parties (lessor/lessee), demised premises, **term + expiry from the deed itself** (NDR's memory of the date is often approximate — he said "end Dec 2027", deed said 31/01/2028; always quote the deed, per P14), rent vs statutory thresholds, SD amount, no-subletting clause.
3. Answer the renewal question clause-by-clause:

## Checklist — tenant's extension rights
- **Fixed-term clause wording.** "For a fixed period ... and on the expiry of the said period, the Lessee shall hand over the actual vacant possession ... **without seeking further extension of time**" (Clause 1) = express NO-extension commitment by tenant. Strong landlord anchor.
- **Search the whole deed for renewal hooks** — "option to renew", "renewal on same terms", "right of first refusal", "mutual consent to extend", "further period", "extended period". Often the phrase "extended period of lease" appears only in boilerplate (SD refund, vacate-on-extended-term) with NO clause creating the right — that contemplates a future mutual extension, not a tenant right. Say so explicitly.
- **Automatic termination on effluxion** (e.g. Clause 20.1 "Expiration of the Lease Term or any renewed term thereof").
- **⚠ THE ONE REAL HOOK — Security-deposit self-help clause.** Mirror-pattern found in Silver tip (Clause 5.5): if the lessor fails to refund the SD (tenant ready to hand over at expiry), the tenant may "continue to occupy the Demised Premises without paying any Rent ... until the Security Deposit along with interest at 18% p.a. is paid." This is the ONLY lawful continuation route. It is a penalty for non-refund, NOT an extension right — mitigation: landowner must be ready to refund SD (after adjusting arrears) SIMULTANEOUSLY with possession handover on expiry day, and cancel the lease deed (many deeds tie SD refund + vacant handover + deed cancellation together — Clause 5.3 pattern).
- **Statutory shield check.** Karnataka Rent Act 1999 applies only to premises with monthly rent ≤ ₹3,500 (BBMP areas / as amended) — a ₹1L/mo lease is OUTSIDE it, so no rent-control tenancy protection; recovery of possession is straight TP Act. Check the actual rent threshold for the state/year.
- **Holding over (s.116 TP Act).** Post-expiry renewal arises only if the lessor ACCEPTS rent after expiry. Instruct the owner: refuse any rent tender post-expiry (or the tenancy may be deemed month-to-month renewed).
- **Operator ≠ tenant.** If the physical operator (brand/franchise) is a different entity than the named lessee, that is a subletting breach (no-sublet clause) — an EARLY termination route for the owner, and worth verifying on site.

## Action plan to give NDR
Written "no extension, possession due on <date>" notice 3–6 months before expiry; simultaneous handover + SD refund + deed cancellation at expiry; owner refuses post-expiry rent; if tenant overstays → tenancy at sufferance → ejectment suit under TP Act (fast when Rent Act doesn't apply).

## Filing
Lease deed → the property's Title folder (e.g. DRA Realty / Millers Road Office Building / Title), named `YYYYMMDD_Property_Type_Parties.pdf` with the DEED execution date (20181201_..., not today).