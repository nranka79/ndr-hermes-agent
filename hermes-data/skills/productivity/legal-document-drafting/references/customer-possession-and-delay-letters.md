# Reviewing DRAAS customer-facing legal letters before issue

Load for: a possession letter, registration-delay letter, allotment letter, car-park
allotment letter, no-dues/NOC letter, or any letter a DRAAS entity signs and gives to an
apartment buyer — especially when NDR says "check the letter", "analyse for errors",
"is this correct or not correct".

These letters become **evidence**. A buyer's CA files them; an assessing officer may read
them. A wrong official document number in one of these letters is a material defect, not a
typo. Review them against the **executed agreement**, not against memory, not against the
CRM sheet.

## NDR's ask pattern (observed 2026-10-05, Ranka Iris)

NDR will ask for several things in one breath: *"check the letter plus whatever the other
document is, rename it, file it appropriately, find the appropriate folder, and most
important analyse it for errors and advise whether it's correct."*

**The analysis GATES the filing.** Do not move a defective letter into the permanent legal
set. Sequence:

1. Extract and read every attached document fully (docx → `python-docx` in `terminal()`;
   scanned PDF → `pdftoppm` + `tesseract`, see pitfalls).
2. Verify each factual assertion against the executed source document on Drive.
3. Stage the **renamed** copies in the root `TMP` folder (standing HARD RULE) and verify
   the upload by reading TMP back.
4. Report the errors, state the folder you would file into, and **hold the move** pending
   NDR's decision. Renaming + staging is safe; filing into the legal set is not.

## The review checklist

Run every letter against this list. Quote the source clause when you flag something.

1. **Official document numbers.** Every sanction / CC / OC / katha / registration number
   cited must match the document it is attributed to. Numbers get copy-pasted across
   drafts in DRA's corpus and swapped between the sanction, CC, OC and khata — see the
   Ranka Iris worked example below. **A number that appears in your own drafts is not
   evidence that it is the number of the document named.**
2. **Issuing authority.** Post-2025 the Bengaluru civic body is the **Greater Bengaluru
   Authority (GBA)** with city corporations (e.g. **Bengaluru Central City Corporation**).
   BBMP-era letterhead language for a 2026 OC is wrong. Check the letter does not call the
   authority BBMP in one paragraph and GBA in the next.
3. **Dates.** Any blank `Date:` field, and any "this day" / "hereby" recital that presumes
   a date. A blank possession date is fatal for the use case below.
4. **Party names.** Compare the addressees and signatories against the **allottee parties
   named in the executed Agreement for Sale**. A co-allottee in the letter who is not a
   party to the AFS creates title ambiguity — check whether a joint-allottee instrument
   exists before signing to it.
5. **Areas** — carpet, super built-up, UDS. Match the AFS Schedule B / recital. Beware the
   CRM master sheet, which carries different (and internally inconsistent) figures.
6. **Consideration.** Must match clause 1.2 of the AFS and the payment schedule, not the
   e-stamp declared value and not the CRM sheet. Say which document you matched.
7. **Possession wording.** "vacant, peaceful and physical possession" vs "possession for
   interiors and fit-out" are different legal positions. Use ONE formulation across all
   letters for the same purpose — the fit-out formulation is weaker and can be read
   against a buyer claiming acquisition.
8. **Car parking.** Count, bay number(s), basement, and area. Bay numbers are frequently
   absent entirely — flag the gap rather than passing it through.
9. **Entity name form.** "DRA Developers & Projects Private Limited" (as in the AFS) vs
   "Pvt Ltd" vs "Pvt. Ltd." — pick the form used in the executed agreement.
10. **Signatory authority** — correct director / authorised signatory, and the board
    resolution behind it.

## The capital-gains use case (why these letters exist)

Where a buyer has LTCG to shelter under s.54 / s.54F and DRA cannot yet deliver a
registered sale deed (khata bifurcation stuck), the CA's advice is to issue a **possession
letter + a delay-explanation letter** as the pair.

- The settled position in ITAT rulings is that the **date of possession can be treated as
  the date of acquisition** for s.54/54F where the deed is unregistered but consideration
  is paid and possession taken. Possession letters and builder receipts are the standard
  evidence the tribunals look for.
- The registration-delay letter's job is to show the missing registered deed is not the
  buyer's fault and the buyer's rights are protected.
- **Because the whole claim rests on these letters, factual precision IS the deliverable.**
  A blank possession date, a wrong OC number, or an unverifiable registration reference
  undermines the claim it was written to support.
- The position is still litigable where the deed is unregistered (the "registered document
  required" view exists) — so never overstate, and recommend the CA confirm the section
  and the exact date basis.

**Ask NDR which customer gets which letter.** A complete CG file needs BOTH the possession
proof and the delay explanation in the SAME buyer's name. If the drafts on the table are
for two different apartments/buyers, say so — do not assume they are one package.

## Worked example — Ranka Iris, 2026-10-05

Two drafts reviewed: a possession letter for Apt 1006 (Aroor Arvind Rao) and a
registration-delay letter for Apt 1008 (Kalpna Oberoi).

**Defect that must not ship — wrong OC number, in BOTH letters.** Both cited
`Occupation Certificate No. BBMP/Addl.Dir/JD North/0037/2013-14 dated 04.06.2026`. That
string is the **building-plan-sanction / LP number** (02-09-2013) — it is literally Ref (3)
printed inside the OC. The real OC is **ACTP/BCCC/OC/001/2026-27 dated 04.06.2026**, issued
by the **Bengaluru Central City Corporation**. See the Ranka Iris project reference under
`draas-drive-organization` for the full trap — the same number is also misused as the
*Commencement Certificate* number inside the executed AFS.

**What was correct** (worth stating so NDR knows what is sound): 1006's carpet 2198.61 sq ft,
super built-up 3775 sq ft, UDS 880 sq ft, and consideration Rs 5,99,66,550 all matched the
AFS clause 1.2 and Schedule B exactly. Names, addresses, floor, unit type, promoter entity
and the authorised signatory were right. The instrument choice itself was sound.

**Other flags raised:** both dates blank (fatal for the CG recital); possession described as
"vacant peaceful and physical" in one letter but "for interiors and fit-out" in the other;
Mrs. Sandhya Arvind Rao addressed and signing as a purchaser although the AFS names only
Mr. Aroor Arvind Rao; the car-park line inherited an internal contradiction from the
agreement ("2.5meters to 5.5mtrs (45 sq ft)" — 2.5x5.5 m is ~148 sq ft, not 45); the
Deed of Declaration registration particulars (04-08-2026, Doc 476/2026-27, Book-4,
Sub-Registrar Indiranagar) could not be verified — only drafts were on Drive.

## Pitfalls

- **Verify a suspected drafting defect at high DPI before asserting it.** A garbled phrase
  in a 150 dpi OCR pass may be an OCR artefact, not a document defect. Re-render the single
  page at 400 dpi (`pdftoppm -r 400 -png -f N -l N`), crop with PIL, re-OCR at `--psm 6`,
  and only then state it as a defect in the document. On the Ranka Iris AFS this turned
  two "possible OCR artefacts" into confirmed defects in the *executed* agreement.
- **The CRM/customer master sheet is not the contract.** It is useful for names, PAN,
  addresses, booking dates and per-apartment owner pairs, but its area and consideration
  columns drift from the executed agreements and are internally inconsistent between rows.
  Match contract figures to the agreement; use the sheet only to corroborate parties.
- **Registry/registration claims need a registered copy, not a draft.** If a letter asserts
  a registration date/document number and only drafts exist on Drive, flag it as
  unverifiable rather than repeating the number as fact.
- **A statement of full satisfaction + no-claims in a possession letter is a waiver.** Check
  the buyer is not being asked to certify satisfaction with an area that is still disputed
  (e.g. while khata bifurcation area figures are unsettled).
- **Name collisions across DRA projects.** Filenames like `SALE AGREEMENT F-1008.docx` and
  `A-1006.pdf` are **Mirabilis** (Kolte-Patil) unit numbers, not Ranka Iris apartments.
  Always confirm a fetched agreement belongs to the project you are reviewing before
  quoting it.
