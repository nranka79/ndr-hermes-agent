# Medication Change Tracking Across Multiple Visits

## Scenario

A patient sees multiple doctors in rapid succession (e.g., over 5–7 days), each adjusting the regimen. This creates confusion if the dossier simply lists all medications chronologically without indicating which are currently active.

## Real Example (Ruhaan Ranka, Jun 2026)

| Date | Doctor | Action | Medication | Rationale |
|------|--------|--------|-----------|-----------|
| 09 Jun | Dr. Vasunethra | STARTED | Predmet 16mg 1-0-0 ×5d | Acute exacerbation |
| 09 Jun | Dr. Vasunethra | STARTED | Forapril neb 0.5mg 1-0-1 ×10d | Acute exacerbation |
| 09 Jun | Dr. Vasunethra | STARTED | Bilasure-20 0-0-1 ×15d | Anti-allergy |
| 09 Jun | Dr. Vasunethra | STARTED | Rablet 20mg 1-0-0 ×5d | PPI cover |
| 10 Jun | Dr. Rohan Naick | CHANGED | Levolin 0.63 + Budecort 0.5 neb | Sequential neb protocol |
| 12 Jun | Dr. Hiremath (ER) | CONTINUED | Predmet extended to 5d total | Incomplete course |
| 12 Jun | Dr. Hiremath (ER) | STARTED | Tusq-DX syrup SOS | Cough suppression |
| 13 Jun | Dr. Bharat Reddy | STOPPED | All nebs | Clinical decision |
| 13 Jun | Dr. Bharat Reddy | STOPPED | Bilasure | Clinical decision |
| 13 Jun | Dr. Bharat Reddy | STOPPED | Rablet | Clinical decision |
| 13 Jun | Dr. Bharat Reddy | STARTED | Junior Lanzol 30mg 1-0-0 ×5d | Replaced Rablet |
| 13 Jun | Dr. Bharat Reddy | STARTED | Foracort 100 pump 2p BD | Maintenance |
| 13 Jun | Dr. Bharat Reddy | STARTED | Levolin pump 2p TID SOS | Rescue |
| 13 Jun | Dr. Bharat Reddy | STARTED | AZEE 500mg 1-0-0 ×5d | Macrolide anti-inflammatory |
| 15 Jun | Dr. Srikanta JT | STOPPED | Bilasure, Rablet, Junior Lanzol | All prior meds discontinued |
| 15 Jun | Dr. Srikanta JT | STOPPED | Foracort 100 (standard-particle) | Replaced with fine-particle |
| 15 Jun | Dr. Srikanta JT | STARTED | Niveoli 120 mcg 1p BD (fine-particle ICS/LABA) | Small airway targeting |
| 15 Jun | Dr. Srikanta JT | STARTED | Fluticone FT nasal spray 1 spray each nostril 6PM | Nasal/ENT component |
| 15 Jun | Dr. Srikanta JT | CONTINUED | Levolin 50 mcg 3p every 4th hr ×3-5d + SOS | Rescue |
| 15 Jun | Dr. Srikanta JT | STARTED | Tab Allegra 120 mg 1 OD ×3-5d | If cold present |
| 15 Jun | Dr. Srikanta JT | ADVISED | HDM SLIT | Start immunotherapy |

## How to Present in the Dossier

### Option A: Compact Treatment Course Table

Use a table with columns: Date | Provider | Medication Changes

In the "Medication Changes" column, use badges: 🟢 STARTED, 🔴 STOPPED, 🔵 CHANGED, ⏩ CONTINUED — followed by the medication name and dose. Keep it compact. Group by date.

### Option B: Active Medication Summary (Recommended)

After the treatment course table, include a **Current Active Medications** section that lists only what the patient should be taking RIGHT NOW, ignoring all stopped/changed medications. This is the most useful view for the next doctor.

Current Active Rx (after 15 Jun 2026):
- Niveoli 120 mcg — 1 puff BD (fine-particle ICS/LABA)
- Fluticone FT Nasal Spray — 1 spray each nostril at 6 PM
- Levolin 50 mcg — 3 puffs every 4th hourly + SOS
- Tab Allegra 120 mg — 1 OD if cold symptoms
- HDM SLIT — pending start

### Option C: Previously Stopped Medications

List medications that were tried and stopped, with reason and date:
- Foracort 100 → replaced by Niveoli 120 (15 Jun)
- Bilasure-20 → stopped (13 Jun by Dr. Bharat Reddy)
- Rablet → stopped, replaced by Junior Lanzol (13 Jun) → then stopped entirely (15 Jun)
- Predmet 16mg → completed 5-day course (13 Jun)
- Forapril neb → stopped (13 Jun)
- All nebs → stopped (13 Jun)
- AZEE 500mg → completed 5-day course
- Junior Lanzol → stopped (15 Jun)
- Tusq-DX → SOS only

## Implementation Pattern

In the HTML dossier template, add both `Current Medications` and `Previously Stopped Medications` tables after the Treatment Course section. This ensures:
1. The timeline is complete (Option A)
2. A doctor can see at a glance what the patient is currently on (Option B)
3. What was tried and failed is recorded for reference (Option C)
