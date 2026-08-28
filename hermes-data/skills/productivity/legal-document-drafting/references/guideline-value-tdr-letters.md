# Guideline Value & TDR Confirmation Letters (Karnataka)

Class: official letters to Karnataka registration/town-planning authorities requesting written
confirmation of guideline value (guidance value / circle rate) for a survey-number-specific land
parcel, and confirmation that the TDR to be loaded is computed on that basis.

## When this applies
- Developer owns a specific survey number (e.g. Sy. No. 14/1, Allalasandra Village, Yelahanka
  Hobli, Yelahanka Taluk, Bengaluru Urban District)
- Needs an OFFICIAL LETTER IN WRITING confirming guideline value before loading TDR / computing
  stamp duty / registering a transaction
- Wants corroboration from the town-planning authority (JDTP / ADTP) that the guideline value is
  final and the TDR value is computed from it

## Two-letter pattern (generated in Aug 2026 session)
1. **L1 → Sub-Registrar** (e.g. Sub-Registrar Office, Yelahanka): request Guideline Value
   Certificate / official letter confirming:
   - guideline value (₹/sq.m or ₹/sq.ft) per current notification under Karnataka Stamp Act, 1957
   - land classification (agricultural / non-agricultural) and guidance-value zone
   - notification reference number and date
   - that TDR value to be loaded will be computed on the basis of that guideline value
2. **L2 → JDTP/ADTP** (Attn: named officer, e.g. Shri Nagrajappa): written confirmation that:
   - the guideline value is the confirmed value adopted by the authorities
   - TDR value is computed on the basis of that guideline value
   - notification reference + method/formula for TDR computation

## Letter structure (python-docx, bbmp_letter_template.py pattern)
- Right-aligned Ref + Date
- To block (designation, office, taluk, district)
- Bold Subject line (must name survey number + village + hobli + taluk + district)
- Salutation "Respected Sir,"
- Body paragraphs:
  - Ownership/possession + survey number + village + "situated immediately outside [Landmark
    layout]" disambiguation if relevant
  - Purpose (development + TDR loading + stamp duty/registration computation)
  - Numbered request items (a/b/c)
  - TDR-computed-on-this-guideline-value confirmation request
- Enclosures (attested RTC copy of the survey number)
- Closing + signature block

## Pitfalls (learned the hard way)
- **CONFIRM SURVEY-NUMBER SCOPE BEFORE GENERATING.** In Aug 2026 the user wrote "Sy No 14/1 to 7"
  then corrected: "Correction Survey No 14/1 only." A range like "14/1 to 7" is ambiguous — it
  could mean 14/1 through 14/7 or 14/1 only. When the request is for a government-authority letter
  (guideline value, TDR, registration), the survey number is the single most important identifier —
  regenerate costs a full docx rebuild. Ask if the range is plural, or generate with the exact
  survey number the user stated first.
- Keep singular/plural grammar consistent with the survey count: "RTC copy" vs "RTC copies",
  "the above survey number" vs "the above survey numbers" — mismatch reads sloppy in a formal letter.
- RTC attachments may not reach the session — the letter is still drafted with "attested RTC copy
  enclosed" as the enclosure line; ask user to resend RTCs if they want extents/owners pre-filled.
- L2 address block: confirm whether the officer is JDTP or ADTP and under which office (BDA vs
  Directorate of Town Planning, Bengaluru Urban) — user said "ADTP or JDTP Nagrajappa", leaving
  designation unresolved; keep both lines or confirm before printing.
