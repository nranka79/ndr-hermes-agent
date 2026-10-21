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
    related_skills: [karnataka-land-title-due-diligence, property-title-due-diligence, real-estate-legal-compliance, legal-document-drafting]
---

# Karnataka Succession Title Chains (Wills / Heirship)

Companion to `property-title-due-diligence` — use that umbrella for general
Karnataka title DD (RTC, MR, EC, khata, document organization). Use this skill
for the SPECIFIC class: "which property did my ancestor buy, by which Will was
it given, and how did the RTC/Pahani change to the heir" (family/legacy
holdings in Doddaballapur / Bengaluru Rural, Chennai, etc.).

This skill owns the Kannada-reading/OCR mechanics for succession (deed
direction, MR Form-12 old-khatedar bridge, 300dpi name disambiguation,
death-date vs Form 10 cross-check). When succession is one workstream inside
a full ground-up multi-document title investigation, use
`karnataka-land-title-due-diligence` Stage 6 for the legal-framework checklist
(signatory authority, shares, personal law, missing heirs) and bring the
mechanics from this skill into it — don't re-derive the reading mechanics
there.

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

## Preliminary title opinion → collection checklist (NDR rule, Gunjur Sy 40 pattern)

When an advocate's preliminary title opinion carries a "documents to be furnished" list, that
list IS the authoritative requisition — propagate it VERBATIM into the colleague collection
task (checkbox list with named people and exact periods), never paraphrase into vague items.
NDR corrected this 2026-09-04: "family trees" → name BOTH persons; "RTCs for gap years" → name
the survey splits AND the gap period; "acquisition endorsements" → name EACH authority.

- **Family trees must name the persons** — e.g. "Attested Family Tree of B. Thippaiah" AND
  "Attested Family Tree of Patel Hanumegowda" (Tahsildar attested), not "attested family trees"
- **RTCs must name the split and the years** — e.g. "RTCs 1979-80 to 1983-84 for Sy 40/P1 and
  Sy 40/P2" (the report's reviewed periods show the gap; state it explicitly)
- **Acquisition endorsements must name each authority** — LPA, KIADB, KHB, and NH/State
  Highway + District Authority (road-widening) as separate items
- **Revenue pack is specific**: Karda (khata), Village Map, Hudbast (Hadbas), Survey Sketch —
  each its own checkbox item
- **Mirror the SAME full list in email draft AND WhatsApp link.** Long lists exceed Telegram's
  4096-char cap → whatsapp_link auto-splits into parts; deliver each part as its own message
- **Voice-name mapping for this chain**: NDR's "Kipaya" = **B. Thippaiah**; "Hanumai Gowda" =
  **Patel Hanumegowda**. Report's death-cert names are **B. & T. Thippaiah** (an earlier draft
  said "D. Thippaiah" — the report is authoritative)
- Extraction recipe + full 22-item Gunjur Sy 40 checklist:
  `references/gunjur-sy40-preliminary-title-opinion-checklist.md`

## GoK Revenue Dept 'Attestation of Family Tree' — the Tehsildar-certified family tree

What NDR calls the "Tehsildar certified family tree" is the **Government of Karnataka, Revenue Department 'Attestation of Family Tree'** (ವಂಶವೃಕ್ಷ) issued by the Deputy Tahsildar on e-stamp paper, verifiable online at nadakacheri.karnataka.gov.in. Certificate numbers look like `RD0039275513038`. The page lists applicant + parents + siblings with Aadhaar last-4s and relationship to applicant, plus a purpose recital (inheritance / dispute / pension / survival certificate). This is the authoritative family-tree document for succession chains — preferred over self-drawn trees, and the document banks/lawyers mean when they ask for a "family tree certificate" (successor-petition drafts are NOT a substitute).

- On NDR's Drive the DR-family attestation is named `DR Family tree GoK Revenue Dept.pdf` (file id 1IWRv3LhtgXxtlIhvJ17Y9GqL4BBekQb-): cert RD0039275513038, dated 28-10-2022, Deputy Tahsildar, City Circle Hobli, Bengaluru North (Addl.) Taluk; lists late Dinesh Ranka alias Dinesh Devraj Ranka, Kanta Ranka alias Kanta Dinesh Ranka, and children Dharmesh, Mamata, Nishant, Manish.
- Search hint: these file under the person's initials ("DR Family tree..."), not the full name — see `document-dossier-compilation` initials rule.

## Two paths — testamentary AND court-based (absorbed from will-succession-title-chains, 2026-09-06)

Succession title work splits into TWO paths; both are handled under this skill:

**Path A — Testamentary (Will-based) chains:** ownership flows testator → successor through a Will.
Reconstruct what the deceased actually held (MR/Form-12 old-khatedar rows), verify each Will recital
against the actual registered deed (recitals can cite the WRONG document — e.g. 1994 Will citing
"Sy No. 41 … Doc 302" when Doc 302 was the Sy 40/2 deed), find the mutation that moved the
RTC/Pahani into the successor's name, and cross-check death dates (mutation applications often state
the Will-execution date instead of the true death date — verify against city-corporation Form 10).
Full worked chains: `references/gunjur-dodballapur-jaravabai-chain.md` (also mirrored as
`references/gunjur-dodballapur-farmland-chain.md`) with document IDs, MR numbers and delivery record.

**Path B — Court-based succession petitions (Indian Succession Act, 1925):** for Letters of
Administration / succession certificates (e.g. Dinesh Ranka estate) — the target is a court-filing
set: LOA, Joint NoC, Vakalat, underlying Family Settlement/Arrangement Deed, Letter of Understanding.
Search BOTH session history and Drive (the LOU may not sit in the same folder as the petition docs).
Full document set, Drive locations and search workflow:
`references/succession-petition-document-discovery.md`; live matter state:
`references/dinesh-ranka-succession-filing.md`.

**Death-cert discovery — index sheet is the source of truth, not Drive fullText:** scanned legal
bundles (NAPS2) have no text layer, so `fullText contains` returns zero hits even when the cert is
inside them. Consult the project's index spreadsheet first (e.g. Allalsandra Northstar "Docs Verified
In MDR Possession" sheet) and cite the exact tab + row — see
`references/allalsandra-northstar-succession-records.md`.

Additional pitfalls observed in will-based tracing: confusing survey numbers under kharab (cultivable
vs total extent differ), same-name relatives (anchor with parentage), a parcel in an earlier Will may
not be in the final holding (check current RTC/MR before claiming), and 150-dpi Kannada misreads
(ಧರ್ಮೇಶ್ vs ದಿನೇಶ್ — re-render contested pages at 300 dpi and read character-by-character).
Typed English Wills read well via vision OCR at 300 dpi; handwritten top-left annotations on deeds
corroborate sale direction. Full methodology preserved in `references/will-succession-title-chains.md`.

## Live family matter (movable assets)

`references/dinesh-ranka-succession-filing.md` — Dinesh D. Ranka (father of
Nishant/Dharmesh) succession-certificate filing: P&SC petition + GPA + vakalat
+ LOU, parties, Law Square counsel, Drive links, review findings and OPEN
FLAGS (vakalat firm name mismatch Ashlar Law vs Law Square, re-date set to
05.09.2026, signature-PDF prep). Re-read before any follow-up on this matter.
**⚠️ Contains the GPA VERSION TRAP (updated 14-Oct-2026): two files are both named
"…GPA… Final.docx" and only the 07-Oct one is correct — the 02-Oct version wrongly
includes MANISH RANKA as a principal. The GPA has only 3 principals (Nishant, Mamata
Ranjeeth Rathod, Kanta) even though the PETITION lists 5 heirs. Printing the wrong
version already caused one rejected signing cycle. Diff `word/document.xml` before
printing or forwarding any version of these documents.**

## Gunjur Sy 40 title opinion — document checklist (live matter)

`references/gunjur-sy40-title-opinion-checklist.md` — BRK Law Preliminary Title
Report (03-09-2026, File 158/25) caveat list — 22 items A–F (grant origin docs,
B. Thippaiah & Patel Hanumegowda family trees, death certs, O.S. 196/1991 file,
MR extracts + RTC gap 1979-80→1983-84 for 40/P1 & P2, Village Map / Hudbast /
Karda / Survey Sketch, LPA/KIADB/KHB/NH+District acquisition endorsements, ECs),
tracker P-119 (row 83, Vinod/Rahul, committed 2026-09-11), email draft id, and
the either-document-or-endorsement rule. Re-read before any follow-up on this
matter.