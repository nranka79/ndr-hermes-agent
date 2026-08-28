# Land Aggregation MOU — Party Restructure & Title Flow (Doddasane case, Jul 2026)

**Trigger:** User asks to remove/consolidate landowners in a dev-cum-sale or
land-aggregation MOU (DRAAS context), or asks to encode a title-flow /
Grama Thana condition-precedent story into an existing MOU's recitals.

Source case: `20260723 Doddasane(next to Airport) - Term_Sheet_9A-FarmPlots-RevShare`
(doc `1vXpNnHl7IjboIA6CSwrW4U08Mo-Coj_TfdP0aGkMyJ4`), a Development-cum-Sale MOU
with 4 First Party landowners + 3 Second Party investors + DRA Realty as
Third Party.

## The restructure pattern

The user's instruction chain (typical of land aggregation deals):

1. **Remove parties literally** — "remove first party 1,3,4 and second party 3"
   means remove First Party No. 1, No. 3, No. 4 and Second Party No. 3.
   **Do not soften the list** just because a role description of FP1 follows —
   that description is the BACKSTORY for a recital, not a reason to keep the
   party. (Prakash corrected exactly this: FP1 was removed too, only FP2
   Muniraju C remained as FIRST PARTY.)
2. **Title flow recitals** describe how land reaches the surviving party:
   - Vendor (non-party) currently owns Sy 68/1, purchasing Sy 68/2 from its
     current owner (name TBD) → on completion, Schedules A & B transfer/release
     to FIRST PARTY.
   - Family members (current joint owners) release Schedules C & D to FIRST
     PARTY.
3. **Schedules follow the party** — every schedule header becomes
   "Land belonging to FIRST PARTY" (party numbers dropped).

## Cascade checklist when removing parties

1. Delete party definition paragraphs (`deleteContentRange`, ranges sorted
   descending by startIndex; verify each boundary first).
2. Collapse/replace the collective definition — if only ONE party remains,
   use single-party definition:
   `(Hereinafter referred to as the "Landowner" or the "FIRST PARTY", which
   expression shall unless repugnant to the context mean and include his
   respective legal heirs, executors, administrators, and permitted assigns);`
3. Renumber surviving parties (e.g. `2.\tSri. MUNIRAJU C` → `1.\t`).
4. Recital A: singularize ("The Landowner (FIRST PARTY) is the absolute ...
   title owner").
5. Add/rewrite recitals H+ for title flow (see language below).
6. Schedule headers: drop "NO. 1/NO. 2" → "FIRST PARTY".
7. Clause bodies referencing "FIRST PARTY NO. 2" → "FIRST PARTY" (e.g. road
   access clause 4.2.2).
8. Signature/witness blocks: delete removed parties' lines.
9. Grep-verify: zero occurrences of removed names (MURALI|SUBRAMANYAIAH|
   NAVEEN) and "FIRST PARTY NO." — including the duplicated-header typo case
   `(Survey No. 68/2 - (Survey No. 68/2 - ...` which got fixed while editing.

## Recital language that worked

- **Vendor purchase + transfer:**
  "Sri. Narasimhaiah is the current landowner of the land comprised in Survey
  No. 68/1 and is in the process of purchasing the land comprised in Survey
  No. 68/2 from its current owner (name and details to be shared later). Upon
  completion of the said purchases, the lands comprised in Survey Nos. 68/1
  and 68/2 (Schedules 'A' and 'B' respectively) shall be transferred and
  released in favour of the FIRST PARTY."
- **Family release:**
  "The lands comprised in Survey Nos. 28/P120 and 28/P110 (Schedules 'C' and
  'D' respectively) shall be transferred or released in favour of the FIRST
  PARTY (Sri. Muniraju C) by the other family members who are the current
  joint owners thereof."
- **Road access facts (already-relinquished vs. future transfer):**
  "The road from the Village Road to the entrance of the Project has already
  been relinquished to the Grama Panchayat as a public road. The road access
  from the entrance of the Project to Survey No. 68, which runs over Survey
  No. 26, belongs to the FIRST PARTY, who shall transfer or relinquish the
  same to the THIRD PARTY or to the Project upon the complete development and
  sale of the Project to the buyers."
- **Grama Thana condition precedent (essence-of-deal):**
  "Plot Nos. 17 and 18, admeasuring about 30 Guntas, forming part of Survey
  Nos. 68/1 and 68/2, are presently within the Grama Thana limits. The Grama
  Panchayat has submitted an application to extend the Grama Thana limits to
  250 metres, and upon such extension being ordered and approved by the
  competent authority (BIAPPA), all the Schedule properties shall fall within
  the Grama Thana limits, which shall enable the buyers to utilise about
  twenty percent (20%) of the plot area for construction of a G+2 structure.
  The completion of this process is the essence of this transaction and a
  condition precedent, for which the FIRST PARTY and the SECOND PARTY shall be
  responsible to get the same done through the competent authorities before
  the THIRD PARTY is satisfied to market and develop the Project further to
  the buyers after all the Conditions Precedent are completed."

## Pitfalls

- **"BIAPPA" vs "BIAAPA"** — Prakash dictated BIAPPA; the authority is likely
  Bangalore International Airport Area Planning Authority (BIAAPA). Use the
  user's spelling but FLAG the possible official acronym in the summary.
- **Duplicate header typos** in schedule lines are common in generated MOUs
  (`(Survey No. 68/2 - (Survey No. 68/2 - ...`); fix while editing the header.
- **Kept boundaries are fine** — a removed person's name may legitimately
  remain in a boundary description (e.g. "NORTH BY: Survey No. 26, Land
  belonging to Narasimhaiaih"). That is not a party reference; don't change it
  unless asked.
- **Corrections are cheap** — after Round 1 (remove FP3/4, SP3) the user
  corrected "FP1 also removed". Always end the summary with the interpretation
  you used so the user can correct in one message; then apply a Round-2 batch
  (delete + replaceAllText) without rewriting the whole doc.
