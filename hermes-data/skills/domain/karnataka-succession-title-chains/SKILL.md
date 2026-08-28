---
name: karnataka-succession-title-chains
description: >
  Trace Wills, heirship and succession-based title chains for Karnataka
  agricultural/ancestral land: map an ancestor's acquisition sale deeds,
  her Wills, and the MR (Mutation Register) / RTC-Pahani change into the
  heir's name. Covers Kannada deed direction reading, Will recital
  cross-validation, and high-DPI Kannada name disambiguation.
metadata:
  hermes:
    tags: [real-estate, title, due-diligence, rtcpahani, karnataka, wills, mutation, succession]
    category: domain
    related_skills: [property-title-due-diligence, legal-document-drafting]
---

# Karnataka Succession Title Chains (Wills / Heirship)

Companion to `property-title-due-diligence` — use that umbrella for general
Karnataka title DD (RTC, MR, EC, khata, document organization). Use this skill
for the SPECIFIC class: "which property did my ancestor buy, by which Will was
it given, and how did the RTC/Pahani change to the heir" (family/legacy
holdings in Doddaballapur / Bengaluru Rural, Chennai, etc.).

## When to Use

- User asks to trace ancestor's sale deeds → Will → mutation into heir's name
- User says "Javrabai"/"Jaravabai"/"Doduballabur"/"Gunjur Farm" style legacy holdings
- User needs "her sale deeds, her Will, and the RTC Pahani change" for a family land parcel

## Workflow

1. **Start with indexes & advocate requisition lists** (spreadsheets like
   `*Farm index`, `*Legal Files Index`, `*Title Prerequisite Checklist`,
   `*Requisition List`). They embed registration numbers (Doc No, Volume,
   Pages, SRO), named mutations, and family-tree/consent items obtained from
   advocates — pre-map the whole chain from them, then verify on documents.
2. **Read the Will's own recitals.** Typed Wills list each bequeathed property
   with the registration details of the deed by which it "stood in my name"
   (e.g. "vide Doc No 514, Vol 1803, p.156, dtd 6-8-1990, SRO Doddaballapur").
   These recitals are the fastest acquisition-deed map — **but they can be
   wrong** (a 1994 Will recited "Sy No. 41 ... Doc 302 ... 20-5-1993" when
   Doc 302 was actually the Sy 40/2 deed). Verify every Will-cited doc against
   the actual registered deed before asserting it.
3. **Direction of a Kannada deed (buyer vs seller):**
   - Narrator voice: `ಆದ ನಾನು` ("being I") + `ಬರೆಯಿಸಿಕೊಟ್ಟ` ("got the deed
     written/taken" = buyer speaking); seller typically introduced with dative
     `ರವರಿಗೆ` and `ಇವರ ಪರ ವಾಗಿ ... ಜಿ.ಪಿ.ಎ. ಹೋಲ್ಡರ್` when acting by GPA.
   - Handwritten margin annotations are strong signals (e.g. "40/2 9A in favor
     of JKM/DR" = buyer is Jaravabai Kundanmal Mehta / Dinesh Ranka).
   - Cross-check against the prior deeds recited inside the deed.
4. **MR (Mutation Register) Form 12 rows are the succession bridge:** old
   khatedar → new khatedar, extent, `ಆದೇಶ ಸಂಖ್ಯೆ` (order no e.g. CE 670/02-03),
   order date, RI confirmation date (often later), mode `ಸ್ವಾಧೀನತೆ ರೀತಿ: ಪೌತಿ`
   (death/inheritance). New khatedar format: `ಧರ್ಮೇಶ್ ಡಿ. ರಂಕಾ ಬಿನ್ ದಿನೇಶ್ ಡಿ.
   ರಂಕಾ ಸಂಬಂಧ: ಮಗ` — **the `ಬಿನ್ <father>` patronymic is NOT the new khatedar**;
   only the name before "bin" is.
5. **Kannada name disambiguation REQUIRES 300 dpi.** At 150 dpi, `ಧರ್ಮೇಶ್`
   (Dharmesh) vs `ದಿನೇಶ್` (Dinesh) and `ಮಗ` vs `ಮೊಮ್ಮಗ` misread easily.
   Re-render the page (`pdftoppm -png -r 300 -f N -l N`) and ask the vision
   model to read Kannada character-by-character before asserting names on a
   mutation/khata/RTC.
6. **Validate death date against the death certificate.** Mutation
   applications carry wrong death dates (a real app said 03-12-1994 — the Will
   execution date; the death cert said 25-03-1995). A Will signed after the
   cited death date is a red flag; check the cert (city corporation Form 10).
7. **Full succession document set:** death certificate, family tree
   (`ವಂಶವೃಕ್ಷ`, often dated with heirs + ages), family consent/NOC letters
   (listed among mutation-application enclosures), mutation application itself
   (Kannada; states sy nos, basis = Will, enclosures).
8. **MR files can be named after the PERSON not the survey** (e.g. "old MR of
   Sy No: 40 of Jawarabai.pdf") — search ancestor names too.

## Voice-name resolutions (NDR, from worked case)

- "Javrabai" / "Jarav Bai" = **Smt. Jaravabai Kundanmal Mehta** (w/o late
  Kundanmal Mehta) — great-grandmother of Nishant & Dharmesh Ranka
- "Doduballabur" / "Dodballapur" = **Doddaballapur** taluk (Bengaluru Rural)
- "Gunjur" = Gunjur village, Tubagere Hobli, Doddaballapur Taluk

## Worked example

`references/gunjur-dodballapur-jaravabai-chain.md` — full verified chain:
Jaravabai's 1990 (Doc 514/1990-91) & 1993 (Doc 302/1993-94) acquisition deeds,
1990 & 1994 Wills, MR 6/2002-03 (CE 670/02-03) mutation to Dharmesh Ranka,
RTC 17-09-2004 in his name, plus caveats and Drive links.