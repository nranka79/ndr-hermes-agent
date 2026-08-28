---
name: will-succession-title-chains
description: >
  Karnataka (and Indian) succession title chains — TWO paths:
  (A) Testamentary: will/testamentary succession where ownership flows
  testator → successor through a Will; reconstruct what the deceased actually
  held (MR/Form-12 old-khatedar rows), verify each Will recital against the
  actual registered deed, find the mutation that moved the RTC/Pahani into the
  successor's name, and cross-check death dates.
  (B) Court-based: succession petition filings under the Indian Succession Act,
  1925 (Letters of Administration, NoC, Vakalat, Family Settlement Deed) —
  find these documents on Drive + session history and bundle/share them.
  Complements property-title-due-diligence (which covers the broader Karnataka
  title flow); this skill holds the will-specific methodology and worked
  examples.</think>
  See references/succession-petition-document-discovery.md for the court-filing
  document set and search workflow.
metadata:
  hermes:
    tags: [real-estate, title, due-diligence, will, succession, mutation, rtc, karnataka, inheritance]
    category: domain
    related_skills: [property-title-due-diligence, legal-document-drafting, karnataka-rera-collector]
---

# Will-Based (Testamentary) Title Chains

Use when: a user asks which properties stand transferred by a Will, which
sale deeds the testator acquired them under, and when/in what mutation the
RTC/Pahani changed to the successor — e.g. "my great-grandmother willed the
farmland to my brother; I need her sale deeds, her Will, and the RTC change."

## The three-layer chain

1. **The Will(s)** — find ALL of them. Testators often execute an earlier
   "Deed of Will" and a later "Last Will" that expressly revokes previous
   wills/codicils. Only the last counts; quote the revocation clause.
   Read every page — bequest items + signatures/witnesses + executor.
2. **What actually stood in the deceased's name at death** — not what the
   Will recites. The Will is drafted by a lawyer and can cite the WRONG
   registered document for a property. Ground truth = the MR/Form-12 extract
   (old-khatedar rows show exactly which Sy Nos + extents transferred) and
   the actual registered deeds (their recitals of prior chain).
3. **The mutation that moved the RTC/Pahani** — the successor's mutation
   application (usually cites Will + death cert + consents of other heirs),
   the MR order (number 6/YYYY-YY, order no, order date, RI confirmation),
   and the resulting RTC in the successor's name (khata no + khatedar +
   MR number cited in column 11).

## Pitfalls (all observed 2026-08-25, Gunjur/Dodballapur)

- **Will recitals are NOT registration facts.** Observed: 1994 Last Will
  cites "Sy No. 41 ... vide Doc No. 302 dated 20-5-1993" when Doc 302/1993-94
  was actually the Sy 40/2 acquisition executed through the testator's
  GPA-holder; the same Will writes the Doc-514 parcel as "Sy 39-40/2". Never
  quote a Will's registration recital without deed + MR cross-verification.
- **Mutation applications state wrong death dates.** Observed: application
  said 03-12-1994 (actually the Will execution date); death certificate says
  25-03-1995. Read the actual death certificate before dating anything.
- **Confusing survey numbers under kharab.** RTC/MR cultivable extents vs
  total extents in a mutation application differ (18A-11G vs 24A-16G for the
  same Sy No) because of kharab. State which extent you mean.
- **Same-name relatives.** One family tree had two "Dharmesh Rankas" (a
  grandson and a great-grandson). Always anchor the person with parentage
  ("s/o Dinesh D. Ranka").
- **A parcel in an earlier Will may not be in the final holding** (e.g. a
  1990 Deed of Will covered Sy 51 which later dropped out). Check the current
  RTC/MR before claiming what the holding is.

## Vision/OCR technique for scanned Kannada+English deeds

- Render at 150 dpi to triage/appeal; re-render contested pages at 300 dpi
  and ask vision for VERBATIM text (survey numbers, parties, doc numbers).
- Character-level Kannada matters: ಧರ್ಮೇಶ್ (Dharmesh) vs ದಿನೇಶ್ (Dinesh)
  is the difference between successor and his father.
- Typed English Wills read well via vision OCR at 300 dpi — ask for Items
  verbatim ("Item No. 1 ... Sy. No.39-40/2 ... vide document No.514").
- Hand-written annotations on a deed's top-left can state direction of sale
  (e.g. "40/2 9A in favor of JKM/DR") — corroborate, don't rely on the OCR
  of the party-recital alone.

## Delivering

- Give the answer as a document chain with Drive links: acquisitions → wills →
  mutation → RTC; cite registration numbers (doc no / vol / pages / SRO).
- Flag verification points explicitly ("Will recital vs register discrepancy —
  cross-check with EC/Index of Lands").
- Offer to bundle the PDFs. If attaching to email: scanned deeds are often
  20–30 MB and exceed Gmail's 25 MB cap — compress with
  `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook` and verify page count.

## Succession petition document discovery (Indian Succession Act, 1925)

When the user asks to find "succession petition" or "succession documents" from earlier sessions (as opposed to tracing a specific parcel's testamentary chain), the target is a court-filing set under the Indian Succession Act for Letters of Administration — typically including LOA, Joint NoC, Vakalat, and the underlying Family Settlement/Arrangement Deed.

See `references/succession-petition-document-discovery.md` — full document set for the Dinesh Ranka estate, with Drive locations, search workflow, and companion documents (Letter of Understanding, FSA Addendum).

## Companion document: Letter of Understanding / Family Cooperation Agreement

Sometimes the succession petition documents sit alongside a **Letter of Understanding and Cooperation** between family shareholders (e.g. Ranjeeth Rathod, Mamata Rathod, Nishant Ranka, Roshni Ranka) covering governance terms like anti-dilution, IPO timeline, and cooperation on Bangalore-side assets. When searching for "cooperation agreement" or "letter of understanding" in succession contexts, search both session history and Drive — the document may not be filed in the same folder as the petition docs.

## Worked example

`references/gunjur-dodballapur-farmland-chain.md` — full verified Jaravabai → Dharmesh Ranka chain with document IDs, MR numbers, and email delivery record.

NOTE: this skill complements `property-title-due-diligence` (the canonical
Karnataka title DD umbrella). If that skill's directory becomes writable, the
will-specific methodology and reference below should be merged into it.