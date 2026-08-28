# Guideline Value / Guidance Value Certificate Letters (Karnataka)

Pattern proven with Prakash (PS) on **Sy. No. 14/1, Allalasandra Village, Yelahanka Hobli, Yelahanka Taluk, Bengaluru Urban District** (Aug 2026). Use for any request to the Sub-Registrar for an official letter/certificate confirming guideline (circle) value, and the companion confirmation letter to Town Planning.

## Trigger
User asks to "verify guideline value by writing to the Sub-Registrar", "get the guidance value in writing", "guideline value certificate", or needs a letter to JDTP/ADTP confirming TDR value basis.

## Non-negotiable user corrections (encode BEFORE drafting)
1. **Applicant capacity**: If the user says "we are the GPA Holders", the letter must open as "We are the GPA Holders, acting on behalf of and duly authorised by the landowners... vide registered General Power of Attorney No. ____ dated ____". NEVER default to "owners / possessors" — confirm who the applicant is (owner / GPA holder / authorised signatory) before drafting.
2. **Land status**: Ask/confirm whether land is converted for residential use. If yes, state it explicitly in the body AND change the classification request to "residential / converted non-agricultural" (not "agricultural / non-agricultural").
3. **Scope limitation**: If the user says the request is "only to get the correct guidance value", strip TDR/stamp-duty/registration language from the Sub-Registrar letter. The TDR-basis confirmation goes in the SEPARATE Town Planning letter, not the SR letter.
4. **Survey range**: Confirm exact survey numbers (user corrected "14/1 to 14/7" → "14/1 only"). Singular vs plural matters — adjust RTC enclosure line ("RTC copy" vs "RTC copies") and all body references.

## Two-letter structure (L1 + L2)
- **L1 → The Sub-Registrar, [Sub-Registrar Office, area], [Taluk], Bengaluru Urban District**
  - Subject: Request for issuance of Guideline Value Certificate / official letter in writing confirming the guideline value (guidance value / circle rate) applicable to Sy. No. X, [Village], [Hobli], [Taluk], [District]
  - Body: identity (GPA holder + GPA ref) → land location (e.g. "situated immediately outside Judicial Layout, Yelahanka, forms part of Allalasandra Village proper") → converted for residential use → "Kindly note that this request is limited to obtaining the correct guideline value" → request a) value per sq.m/sq.ft, b) land classification + guidance-value zone, c) notification ref/date
  - Enclosures: attested RTC copy, optional village map/sketch
- **L2 → The Joint Director of Town Planning (JDTP) / Assistant Director of Town Planning (ADTP), Attn: Shri [Name]**
  - Subject: Confirmation of guideline value and basis of computation of TDR value
  - Body: same land identity → "We have separately applied to the Sub-Registrar..." → confirm a) guideline value is the confirmed/adopted value, b) **value of TDR to be loaded is computed on the basis of this guideline value**, c) notification reference and method/formula for TDR value
  - Keep the TDR language HERE — never in the SR letter when scope is limited

## Build mechanics
- python-docx letter template: reuse the pattern from `scripts/bbmp_letter_template.py` (right-aligned Ref/Date → To block → bold Subject → body → enclosures → signature)
- Signatory block: "[Name of GPA Holder]" / "GPA Holder, on behalf of the Landowners" — NOT "Authorised Signatory"
- Leave placeholders in [brackets]: GPA No./date, applicant name, ref/date, bank branch if any
- Deliver as .docx via MEDIA: path; do not upload to Drive until user confirms

## Pitfalls
- The RTC attachment may not actually reach the agent — say so, draft anyway, keep RTC as enclosure line #1.
- If the JDTP vs ADTP designation is uncertain, address both lines ("The Joint Director of Town Planning (JDTP) / Assistant Director of Town Planning (ADTP)") with Attn: name, and ask user to confirm the exact office (BDA vs Directorate of Town Planning) before despatch.
- Keep the "immediately outside [Layout]" location clarification in the letter — it prevents the wrong guidance-value zone being applied.
