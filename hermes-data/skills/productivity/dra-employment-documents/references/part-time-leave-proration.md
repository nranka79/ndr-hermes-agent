# Part-Time / Hybrid Leave Proration — Sinchana Gouda Case (Feb 2026)

The reference case for part-time/hybrid employment documents at DRA Group. User rule: part-time employees get **half** the full-time leave entitlements (12 CL → **6 paid**, 10 SL → **5 sick**), and the offer/agreement must carry a specific clause stating exact amounts + the deviation rationale.

## Source documents

| Document | Details |
|---|---|
| `01022026_Shinchana_EmploymentContract.docx` | File ID `1TK80jjxw8IjJYwowm3iVrr3HtgY1KPEH`. Trubld Integrated Services Pvt Ltd (CIN U74999KA2021PTC144888, Prizm Greystone, Cunningham Rd). Employment Agreement dated 1 Feb 2026. **Filename misspells "Shinchana" — actual name Sinchana.** |
| `Sinchana S.pdf` (resume) | File ID `1wbDgcL-tSWwGaXgv3cdmnOPgEJ8hvD7w`, in naukri Architects folder (`1YdCJyS9tyMqaYOJPt8xpHr9k05jJGDai`). B.Arch BMS School of Architecture, Bangalore (2017-2022); RNG Architects Aug 2022–; JASS Associates Feb–Jul 2022. |

## Contract facts (as found)

- **Role:** Senior Architect, reports to The Board of Directors
- **Term:** commenced 2025-09-01
- **CTC:** INR 300,000 per annum (₹25,000/mo), paid 10th of following month, Bank of Baroda
- **§2.3 Timesheets:** mandatory daily, min 4 hrs/day, min 25 hrs/week — payroll based on actual timesheets
- **§4.1 Working Hours:** 12:00 PM–5:00 PM Mon–Fri, 1-hr lunch (1–2 PM) = **4 hrs work/day**
- **§4.2 Weekly:** 20 hours (Mon–Fri), Sat/Sun rest
- **§4.4 Location:** 3 days/week at office (Prizm Greystone) **5 hours**, WFH remaining 2 days
  - ⚠️ **Internal contradiction:** §4.1 says 4 hrs/day; §4.4 says 5 hrs at office. Flag to user — which is authoritative?
- **§5 Leave (as drafted — FULL-TIME numbers, wrong for part-time):**
  - 5.1 Earned Leaves: 12 per annum (accrue 1/month)
  - 5.2 Sick Leaves: 10 per annum (paid)
  - 5.3 Uninformed absences (2-day wage deduction per instance, 3rd → termination risk)
  - 5.4 Carry-forward per policy, encashment only on termination
  - 5.5 Public holidays (GoI + Karnataka)
- **§10 Termination:** 90 days notice (without cause); 30 days (performance); immediate for ethics violations

## HR Policy 2026 (full-time baseline) — file `0BymF3UUrZZYKMnBodl9ILVRVb3c`

- §6 Leave: Casual/Earned **12 days**, Medical/Sick **10 days**, Public holidays
- Business hours: 8 hrs/day Mon–Fri + 6 hrs Sat, 10:00 am–6:30 pm
- Casual leave: 1 day/month earned, max 3 days at a time (3+ days needs 3-weeks-prior approval), post-probation earning
- Medical: 10 days/yr, full pay, proof needed >2 days, unused cannot be carried/encashed
- Long-weekend extension needs 7-day prior approval; ad-hoc sick leave after long weekend not acceptable; 2X deduction for unauthorised leave

## Proposed amendment (approved pattern)

Replace §5.1/§5.2 quantities and add:

> **Leave Entitlement (Part-Time Schedule):** Your leave entitlement under this Agreement deviates from the DRA HR Policy, which applies to full-time employees working 8 hours per day. Given your part-time arrangement — 3 days at office and 2 days remote, ~4 hours of work per day (~20 hours per week) — you shall be entitled to:
> - Paid (Earned) Leave: **6 days per annum** (half of the full-time entitlement of 12)
> - Sick Leave: **5 days per annum** (half of the full-time entitlement of 10)
>
> All other leave terms (accrual, encashment, public holidays, advance application) remain per the HR Policy and the remainder of this Agreement.

## Search recipe that worked

`name contains 'Sinchana'` missed the contract (filename is `Shinchana`). The hit came from `fullText contains 'Sinchana'`. For candidate docs always run: `name contains 'X' OR name contains '<misspelling variants>'` plus `fullText contains 'X'`. Drive is on NDR's account → `build_service('drive', 'v3', service_name='google-draas')` (bare call throws VaultNoTokenError).
