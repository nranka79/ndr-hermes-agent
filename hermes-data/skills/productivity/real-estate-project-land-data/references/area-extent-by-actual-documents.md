# Area / Extent Harness — Go by the ACTUAL DOCUMENT, Never the Opinion Summary

NDR rule (23 Sep 2026, Ranka North Star): *"Let's not go by the area... the area in the
opinion doesn't matter. We have to go by actual documents. If the e-khata is for 53,089
square feet, let's just go with that."*

## What this means operationally

- When stating an extent on a REGISTRABLE instrument (GPA, addendum, sharing agreement),
  the source is the **eKhata certificate** (has a text layer — poppler/pymupdf extracts it
  cleanly; no OCR needed), then the registered deeds (JDA recitals, sale deeds, amalgamation
  deed), then the title opinion LAST.
- Title opinions and JDA narrative recitals are routinely ROUNDED or OCR-garbled. In the
  North Star file the eKhata says **53,148 sq ft** while the JDA/opinion recital says
  "approximately 53,089 or 1 acre 8½ guntas" — the per-site schedule inside the same opinion
  sums to 53,148. The eKhata and the site-schedule agree; 53,089 is the narrative outlier.
- If the user says "use the eKhata figure", READ the eKhata first and quote its exact figure
  even if it differs from what the user said ("khata seems to have 53089"). Correcting with
  the actual doc is expected and appreciated — the user's instruction is conditional on what
  the eKhata actually says.
- Older-style land measurement: eKhata shows Site Area in Sq.Mt + Sq.Ft (4,937.6 Sq.Mt /
  53,148 Sq.Ft for the amalgamated property). ePID + Document No. identify it uniquely.

## Allalasandra / Ranka North Star extent ledger (Sep 2026, verified)

- Amalgamated property (Sites 1-8, JDA 3034): Property No. 591/1077/14/1/1, ePID 4457904186,
  eKhata Doc 2844641, **53,148 sq ft** (4,937.6 sqm), Vacant Site, joint owners: Lakshmi
  Vaidyanathan, R Geeta Swaminathan, Sunder Padmanabhan, Kankshita Swaminathan, V Swaminathan,
  Sreeraman Vaidyanathan, A S Vaidyanathan.
- Per-site extents (sum = 53,148): S1 9,600 · S2 7,952 · S3 5,970 · S4 6,077 · S5 6,087 ·
  S6 5,118* · S7 5,307 · S8 7,037 (*opinion schedule shows 5,118; DRA share sheet 5,115 —
  3 sq ft variance, use the schedule basis).
- Site 10 (separate JDA 3033): Property No. 570/1084/14/1/10, ePID 5839585365, eKhata Doc
  2807266 (13.02.2026), **12,106 sq ft** (1,124.7 sqm), sole owner Kankshita Swaminathan.
- Kankshita's UDS in the amalgamated property: 10,422 sq ft = **19.61%** (S6 4,015+1,100
  passage=5,115, S7 4,207+1,100=5,307). DRA share workbook also carries 22.29% "as per LO"
  and 18.69% "as per us" — those are negotiation positions, not title; use 19.61% on the
  eKhata basis.
- Amalgamation deed: 04.02.2014, Doc BNG(U)BYP/6647/2013-2014 → one khata, joint owners with
  UDS; site identity survives only as share derivation.
- JDA 3034 (Sites 1-8): 07.02.2014, Doc 3034/2013-14, SRO Malleshwaram. Assignment:
  15.03.2021, Doc 5695, SRO Malleshwaram → DRA Ranka Holdings.
- 1 Acre 28 Guntas is the PARENT survey (Sy 14/1 per MR 36/1980-81), not the project holding.
  Project land = 1 acre 8½ guntas; 1993 partition split Sy 14/1 into 1 acre 16½ guntas.

## GPAs for NRI landowners — structure convention

- Two GPAs: one for the UDS in the amalgamated 1-8 property, one for the sole-owned Site 10.
  Never bundle an exit instrument (Site 10: termination/sale/release) with the live-project GPA.
- Draft from the executed addendum's party recitals (authoritative for names, ages, Aadhaar)
  — e.g. V Swaminathan, s/o late R Venkataraman, age ~82, Aadhaar 3176 0609 8349 (NOT the
  figure an earlier session cited from memory). If a particular isn't in any document, leave a
  placeholder — never bake in an unverified number.
- Standard power set NDR expects in a GPA: sell, mortgage/charge/encumber, gift, relinquish/
  release (incl. to "any government, statutory or parastatal authority"), receive consideration
  in the name of either principal or attorney, into either's bank account, cash or kind, plus
  the "deal with property in any manner" sweep clause. Edits to a Google Doc land in BLUE
  (see gws-automation references/docs-api-blue-amendments-and-verification.md).
- An unregistered 2003 GPA does not satisfy current SRO practice — a fresh GPA executed in the
  US, attested (consulate via VFS, OR US notary + apostille — CONFIRM which the Bangalore SRO
  accepts first; the two routes differ by a 4-hour trip), couriered, then adjudicated before
  the District Registrar, is the standing requirement.