# Multi-Prescription Synthesis Workflow

## Trigger

User uploads or references **multiple sequential prescriptions** from different doctors/hospitals and asks for a unified medication schedule — understanding that each subsequent prescription may override, update, or replace parts of earlier ones.

**Typical scenario:** A child with asthma exacerbation visits multiple doctors over 3–5 days. Each doctor adjusts the treatment based on the evolving clinical picture. The user (parent) needs a single coherent schedule showing what to take and when.

## Workflow

### Phase 1 — Collect All Prescriptions in Chronological Order

1. **Identify all documents** — prescriptions, OPD records, pharmacy invoices, verbal prescription notes on Drive
2. **Order by date** — the actual document date (not the upload/scan date):
   - `YYYYMMDD_Ruhaan_..._DrVasunethra_Prescription.pdf` → 9 Jun
   - `YYYYMMDD_Ruhaan_..._DrRohanNaick_VerbalPrescription.txt` → 10 Jun
   - `YYYYMMDD_Ruhaan_..._BMJ_Prescription.pdf` → 12 Jun
3. **Extract key data from each** — medications, doses, schedules, durations, special instructions

### Phase 2 — Understand the Override Chain

Prescriptions are **NOT additive** — later prescriptions override earlier ones for the same medication category. The override logic:

| Medication Category | Rule |
|---|---|
| **Same drug, same dose** | Later prescription continues the course (cumulative duration) |
| **Same drug, different dose** | Later dose replaces earlier dose (e.g., Predmet 16mg → subsequent additional Predmet 16mg = continuation) |
| **Same class, different drug** | Later drug replaces earlier drug (e.g., Duolin → later Levolin means Levolin is the current rescue neb) |
| **New drug not in earlier Rx** | Added to the regimen |
| **Explicit discontinue** | Listed as "stop X" or "switch to Y" |

**Override notes for different prescribers at different facilities:**
- An **ER doctor** addresses the acute crisis — their changes (e.g., stronger bronchodilator, additional steroid doses) are typically **short-term additions** for the acute phase
- A **consulting specialist** (pulmonologist) sets the longer-term plan — their maintenance drug choices override the ER's if there's a conflict
- A **telephonic consultant** gives interim advice — may be explicitly temporary until the regular doctor reviews

### Phase 3 — Identify Override Conflicts

For this session's example (Ruhaan asthma exacerbation, Jun 2026):

| Category | Dr. Vasunethra (9 Jun) | Dr. Rohan Naick (10 Jun) | BMJ ER (12 Jun) | Resolution |
|---|---|---|---|---|
| **Nebulization** | Forapril 0.5mg 1-0-1 × 10d | Levolin 0.63 + Budecort 0.5 back-to-back | Duolin + Budate (ER) | Dr. Rohan Naick's switch overrides for ongoing management. BMJ's Duolin was for acute ER use only. |
| **Oral Steroid** | Predmet 16mg 1-0-0 × 5d | (continues same) | Additional Predmet 16mg × 3 tablets + taper plan | Predmet course continues. BMJ added extra tablets for the same course. Taper plan from BMJ. |
| **Cough** | (none) | (none) | Tusq-DX syrup SOS | Added from BMJ |
| **Stomach protection** | Rabet 20mg 1-0-0 | (continues same) | (none mentioned) | Continue as per original |
| **Long-term inhaler** | Foracort MDI after 10 days | (same plan) | (none mentioned) | Unchanged — start after neb course ends |

### Phase 4 — Build the Unified Schedule

Present as a structured timeline with these columns:

| Medication | Dose | Timing | Duration | Source | Notes |
|---|---|---|---|---|---|
| Predmet 16mg | 1 tab morning | After food | Days 1–5 (9–13 Jun) | Dr. Vasunethra | Then taper per BMJ |
| *(Taper)* 8mg | 1 tab morning | After food | Days 6–9 (14–17 Jun) | BMJ/Hiremath | Half dose |
| *(Taper)* 4mg | 1 tab morning | After food | Days 10–13 (18–21 Jun) | BMJ/Hiremath | Quarter dose |
| Rabet 20mg | 1 tab morning | Before food | 5 days (9–13 Jun) | Dr. Vasunethra | Stop with Predmet |
| Levolin 0.63mg neb | AM + PM | Back-to-back with Budecort | 10 days (10–20 Jun) | Dr. Rohan Naick | Replaces Forapril |
| Budecort 0.5mg neb | AM + PM | Immediately after Levolin | 10 days (10–20 Jun) | Dr. Rohan Naick | Gargle after |
| Bilasure-20 | 1 tab night | Before food | 15 days (9–24 Jun) | Dr. Vasunethra | Continue |
| Tusq-DX syrup | As needed | For cough | SOS | BMJ/Hiremath | Stop when cough settles |
| Levolin 0.63mg neb SOS | Up to 4x daily | For severe breathlessness | As needed | Dr. Vasunethra | Rescue only |
| Foracort 100mcg MDI | 2 puffs AM + PM | Daily maintenance | After neb course ends (~21 Jun) | Dr. Vasunethra | Long-term |

### Phase 5 — Show the "What Changed When" Narrative

Include a timeline explaining the override chain in plain language:

```
9 Jun (Dr. Vasunethra): Started Predmet 16mg, Forapril neb 1-0-1, Bilasure, Rabet
10 Jun (Dr. Rohan Naick): Switched nebulization from Forapril to Levolin 0.63 + Budecort 0.5 (back-to-back, AM+PM)
12 Jun (BMJ ER): Added Tusq-DX for cough. Prescribed 3 additional Predmet 16mg tabs (continuing the same 5-day course). Advised taper after day 5.
```

### Phase 6 — Separate Active vs. Completed Items

- **Active:** Currently being taken (Predmet taper, Levolin+Budecort neb, Bilasure)
- **Completed:** Finished courses (Predmet 16mg full-dose days)
- **Pending:** Starting later (Foracort MDI after neb course ends)
- **SOS:** As needed (Levolin rescue, Tusq-DX)

### Key Pitfalls

- **Early prescriptions may be on their own timeline** — Dr. Vasunethra said 5 days of Predmet, but BMJ gave 3 more tablets. These are probably meant to extend the same 5-day course (replacing missing days), not add days. Confirm with the user.
- **ER prescriptions are acute-focused** — The BMJ ER doctor prescribed Duolin (stronger than Levolin) for the acute crisis. This doesn't necessarily override the specialist's choice for ongoing management. Always distinguish acute vs. maintenance.
- **Verbal prescriptions have limited detail** — Dr. Rohan Naick's advice was telephonic and didn't specify duration. The user interpreted it as "morning and evening nebulization" — confirm the frequency with the user.
- **Taper plans may conflict with evidence** — The BMJ doctor's taper plan (8mg × 4d → 4mg × 4d) is conservative. Research evidence (GINA guidelines, Cochrane review) supports abrupt cessation after ≤7 days of OCS. Present both the doctor's plan AND the research so the user can make an informed decision.
