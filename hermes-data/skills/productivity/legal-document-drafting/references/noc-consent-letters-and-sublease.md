# NOC / Consent Letters for Registered Office & Sub-Lease (DRA Group)

Session-verified workflow (Sep 2026): O3 Infotech NOC → DRA KAAJ Development Partners
for registered office at Prizm Greystone, plus partner-resolution CTC edit on the same premises.

## When to use
- User asks for a "NOC", "No Objection / consent letter", or authority-to-sub-lease letter
  to submit to the Registrar of Firms / any statutory department / bank.
- Registered-office / principal-place-of-business change for a DRA group partnership firm.

## Two shapes — DETAILED vs BASIC (user preference, 2026-09-10)

Prakash explicitly rejected the detailed 3-page NOC shape below ("update this NOC with
very basic information not the detailed one like this") — this was for an O3 Infotech →
DRA KAAJ registered-office NOC to the Registrar of Firms (Google Doc
`1emDAJJ95fkzupOh10fi5x-yNOKsisNyu3Kn82ME3oRE`, simplified in place).

**Rule: for Registrar/statutory NOCs, DEFAULT TO THE BASIC shape unless the user asks
for the full one.** Basic NOC structure:
- Title NO OBJECTION CERTIFICATE (14pt bold, centred) · Date · TO WHOMSOEVER IT MAY
  CONCERN · Re: line (premises + beneficiary + purpose)
- ONE party-identification paragraph: issuer legal name + CIN + registered office;
  lessee status; premises (unit/floor/building, extent, car parks); Lease Deed date +
  lessor
- ONE no-objection paragraph: beneficiary firm (registration no. where issued) +
  authority (Registrar of Firms / any statutory authority)
- Purpose-limited closing ("issued for the above purpose only, and without prejudice
  to our rights under the Lease Deed")
- Signature block: For M/s … / Authorised Signatory / Name / Designation / Place /
  Date / (Company Seal)
- NO WHEREAS recitals, NO numbered clauses A–F, NO Schedule annexure. The detailed
  build below remains the fallback when he asks for the full version.

Rules that apply to BOTH shapes: keep the lease-deed sublet-clause check and the
issuer/beneficiary identifiers (CIN/PAN/lease date/extent) verbatim — simplify the
LAYOUT, never the facts. When the source is a Google Doc (not .docx), do the rewrite
with the Docs API full-body replace pattern (delete body except final `\n`, insert,
then format) — see bank-apf-project-approval → `references/docs-api-cell-fill-pitfalls.md`
point 7; remember `fontFamily` is not a valid textStyle field (use `weightedFontFamily`)
and check namedStyles for the inherited font before fighting run-level fonts.

## Owner/lessor-issued NOC — MINIMAL variant (user correction 2026-09-15)

When the property OWNER (lessor) issues the NOC — the cleanest remedy from the
sublet-clause pitfall below — the draft must be MINIMAL. Prakash's explicit
correction after a first over-filled draft: **"don't give any reference to O3 &
Prizm lease agreement, just the office address and Owner details, as owner is
issuing this NOC for Both."**

Rules for owner-issued NOCs (the tenant-side rules above do NOT apply):
- **NO lease-deed references** (no "as per Lease Deed dated …", no lessor→lessee recital)
- **NO PID/municipal numbers, NO extent/car-park details** — address + owner identity only
- Owner line: `I, <Name>, being the Managing Partner of M/s. <Owner Firm> (PAN ……),
  being the owner of the property situated at <Units, Floor, "Building", Road,
  City – PIN>, hereby give my complete consent and have no objection to
  M/s. <Beneficiary Firm> using the above-mentioned property address as its
  Registered Office Address{ (new address)}`
- Signature block = Signature of Property Owner / For <Owner Firm> / Name /
  Designation / Mobile No. — leave Date, Mobile No., signature blank

**FULL-DETAILS owner variant — explicit user request (2026-09-16, same day as the MINIMAL
correction):** when Prakash asks to "fill in all the details / make a specific mention",
he wants the O3/lease chain restored even in the owner-issued NOC. This SUPERSEDES the
no-reference rule for that request. Same 1-page template (To: District Sub-Registrar /
District Registrar, Shivajinagar → bold Subject → consent para), then ADD in the owner's
voice, in order:
- Lease-chain paragraph: "I have entered into a Lease Agreement with M/s. O3 Infotech
  Private Limited (CIN U74999KA2016PTC094763, PAN AAACZ9777G) in respect of the said
  premises and, to my knowledge, O3 Infotech has subleased the said premises to M/s. DRA
  Realty Private Limited. O3 Infotech is a hundred percent (100%) subsidiary of M/s. DRA
  Realty Private Limited."
- Rentals paragraph (verbatim requirement): "I specifically confirm and mention that the
  rentals in respect of the said premises have already been given/paid and there are no
  outstanding dues in respect thereof."
- Purpose paragraph: "I have no objection to the said premises being used by them for any
  purpose, including but not limited to ABC, TAN and other purposes, and I have no
  objection to them using the premises for business purposes." (Keep "ABC, TAN" verbatim —
  don't expand or drop; user demands explicit mention.)
- Update the SAME Drive file ids in place (`files().update`) so delivered links never
  change. Re-download + re-extract to verify before delivering.

Prakash's own uploaded template shape for these (1 page, follow it when he
provides the .docx):
`NO OBJECTION CERTIFICATE` (bold, centred) → `To, The District Sub-Registrar /
District Registrar / Shivajinagar, Bengaluru` → bold Subject line (NOC for use of
property address as Registered Office Address) → consent para → "I confirm that I
have no objection… for registration and other official purposes" → enclosure para
(proof of ownership: "Property Sale Deed / Khata Document / Electricity Bill
standing in the name of <Owner Firm>") → "This NOC is issued at the request of the
partnership firm for submission before the concerned authorities" → Place/Date →
Signature of Property Owner / Name / Mobile No.

Same-owner two-beneficiary pattern (worked 2026-09-15): one owner (M/s. Prizm
Developers, PAN AAOFP4055G, Managing Partner Mr A.R. Mohammed Abdullah; premises
Unit Nos. 204, 205 & 206, Second Floor, "Prizm Greystone", Cunningham Road,
Bengaluru – 560 052) issuing for BOTH M/s. DRA KAAJ DEVELOPMENT PARTNERS (subject
notes "New Address") and M/s. R3N KAAJ DEVELOPMENT PARTNERS ("office address").
Build the second by changing ONLY the beneficiary + subject. Deliver .docx via
python-docx (A4, TNR 12) and update the SAME Drive file id (`files().update`) on
revision so the delivered links stay live.

## Critical pitfall — ALWAYS read the source lease deed for the subletting clause first
Do NOT draft the tenant's NOC on assumption that the tenant can freely sublet. The
lease deed may restrict subletting:
- Real case: Prizm Developers ↔ O3 Infotech lease deed dated 14-Feb-2023 (Drive:
  `20230214 Lease deed b/w Prizm & O3 Infotech.pdf`, id 1s6SHbFPzGqetxyWzETHhcgDoyT9Lbiyc).
  Clause 9(d) permitted sublet ONLY to O3's associate company Westbury Hospitality Pvt Ltd.
  Subletting to DRA KAAJ (a third party) fell OUTSIDE the lease's express permission.
- Clause 9(f) required any change to the deed to be by a REGISTERED ADDENDUM by all parties.
- Consequence: a tenant NOC alone may not hold up. Offer the user two options:
  1) parallel NOC/consent from the LESSOR (cleanest — they own the premises)
  2) registered addendum treating the sublessee as an associate, if the parties intend that
- Search patterns for finding the clause in pdftotext output:
  `sub-let|sublet|assign|part with possession|associate company|permitted assigns`

## Extraction from the lease deed (before drafting)
1. Find deed on Drive: `fullText contains 'O3 Infotech'` / `name contains 'Prizm'` + 'lease'.
2. Download PDF via `build_service('drive','v3', service_name='google-draas')` +
   `MediaIoBaseDownload` (run via terminal with `HERMES_SESSION_USER_ID=psingh`).
3. `pdftotext -layout` → extract:
   - LESSOR exact legal name + PAN + representative (e.g. M/s Prizm Developers, PAN AAOFP4055G,
     Managing Partner Mr A.R. Mohammed Abdullah)
   - LESSEE exact legal name + PAN + CIN + registered office + Director
     (e.g. O3 Infotech Pvt Ltd, PAN AAACZ9777G, CIN U74999KA2016PTC094763,
     Regd off 4th Fl, No.4, Ranka Chambers, 31 Cunningham Road, B'lore-560052,
     Director Mr Manjunath Manohar Singh)
   - Scheduled premises (unit nos, floor, building, extent sqft, car parks, PID / municipal nos)
   - lease term (start/end dates) and whether it is valid and subsisting as on date

## Google Docs technique — insert a new resolution/agenda item with formatting MATCH
Used when adding e.g. "CHANGE OF ADDRESS OF THE REGISTERED OFFICE" to a partner-resolution CTC.
1. `documents().get()` — list body content with startIndex/endIndex per paragraph.
2. Inspect paragraphStyle + textStyle of EXISTING agenda headings and resolution paragraphs
   to copy: headings = bold, Times New Roman 12, alignment START, spaceBelow 5pt,
   indentFirstLine -18pt, spacingMode COLLAPSE_LISTS; resolutions = justified, spaceBelow 7pt,
   indentFirstLine 0, NOT bold.
3. `batchUpdate` in one call:
   - `insertText` at the index of the blank paragraph before "CERTIFIED TRUE COPY"
     (or after the last resolution paragraph)
   - `updateParagraphStyle` + `updateTextStyle` for the heading range and each resolution
     range, with explicit `fields` masks (bold,fontSize,weightedFontFamily /
     namedStyleType,alignment,lineSpacing,spacingMode,spaceBelow,indentFirstLine,indentStart)
4. Verify: re-fetch doc, print each paragraph with first-run bold flag; then export PDF via
   Drive `files().export` and render-QA pages with pdftoppm + vision_analyze.

## NOC document structure (python-docx, A4, Times New Roman 12)
- Title: NO OBJECTION CERTIFICATE; sub-line "(Under the Indian Partnership Act, 1932)"
- Date/Place right-aligned
- Addressee: "TO WHOMSOEVER IT MAY CONCERN / THE REGISTRAR OF FIRMS, KARNATAKA / ANY STATUTORY AUTHORITY"
- Re: line (premises + beneficiary firm + purpose)
- Party identification paragraph (issuer legal name, CIN, PAN, regd office, authorised signatory)
- WHEREAS recitals (numbered 1-4): lease under which issuer holds possession; term; beneficiary
  firm's registered-office intent; issuer's competence
- "NOW THIS NO OBJECTION CERTIFICATE WITNESSETH AS UNDER:" numbered letter clauses A–F
  (consent to use/occupy/sub-lease; no-objection to registration at premises; no encumbrance
  declaration; purpose limited to Registrar/statutory filing; without prejudice to lease;
  notices address)
- Request line, Yours faithfully, signature block (For M/s... / Authorised Signatory / Name /
  Designation / Company Seal)
- SCHEDULE OF THE PREMISES annexure on page 2 (unit, floor, building, address, extent, car
  parks, municipal/PID numbers, occupancy source, "forms part of" note)
- Use ITALIC/underlined markers where user must fill date; leave "Date: ____, 2026".

## Sibling-firm mirror NOC (reuse the original, change the beneficiary)
Real case (Sep 2026): right after the O3 → DRA KAAJ NOC was delivered, user asked
"Generate a Similar NOC For R3N KAAJ Development Partners". Workflow that worked:
1. Recover the ORIGINAL NOC text. The delivered .docx may still be on disk
   (e.g. /tmp/O3_Infotech_NOC_Sublease_DRA_KAAJ.docx) but /tmp is transient — the durable
   source is session_search("NOC O3 Infotech DRA KAAJ Prizm lease"); the assistant's delivery
   message carries the full text. Extract docx text with python-docx when the file exists.
2. Pull the sibling firm's entity particulars from prior sessions / its partnership deed
   (session_search "<firm name> partnership deed"). R3N KAAJ worked example below.
3. Rebuild the docx with python-docx — same A4/TNR-12 shape (start from
   templates/noc-consent-letter-builder.py), changing ONLY:
   - Re: line beneficiary firm
   - issuer party-identification paragraph UNCHANGED
   - WHEREAS 3: beneficiary description + intent ("establish / shift its Registered Office …")
   - clauses A, B, D: beneficiary name
   - Schedule note line: "in favour of <beneficiary>"
   - filename: <Issuer>_NOC_Sublease_<BENEFICIARY>.docx
4. Repeat the Clause 9(d) sublet-restriction flag VERBATIM for every sibling firm — never assume
   the user remembers it from the prior delivery. Same two remedies (lessor NOC / registered addendum).
5. Pre-delivery checks: re-extract text and assert — beneficiary present, the OTHER previous
   firm's name ABSENT, issuer CIN/PAN present, lease date, clause letters A–F, schedule PIDs,
   "Registrar of Firms". Then render QA (Verification section). Expect 3 pages for this NOC shape.

### R3N KAAJ Development Partners (entity block for future documents)
- Partnership firm under the IPA 1932, established 28.07.2026. As of Sep 2026 NOT YET registered
  with the Registrar of Firms (partnership deed Art 1.4: Form-A within 30 days of execution) →
  omit firm registration no./PAN in NOC recitals, leave fill-in blanks.
- Partners: (1) M/s. DRA Realty Private Limited (CIN U70100KA2011PTC058105, regd off
  201A/202BA, Queens Corner, No. 3, Queens Road, Bengaluru – 560 001) — Sole Managing Partner,
  represented by Mr. Nishant Dinesh Ranka (PAN AHVPR5168E, Aadhaar 4159 0535 2796);
  (2) Mr. Ashok Kumar (S/o Ram Kumar, ~55 y, B-27, Zonasha Paradiso, Doddanekundi, Bengaluru –
  560 037, PAN ANBPK6960D, Aadhaar 8751 3355 3386).
- Partnership deed (no Schedule attached): Google Doc 1hSQKC7UTFNc-ZaIvVUXIHb-AbueHhlUAAXLxb0oLoOQ
  (20260811 session). 51:49 profit share (DRA:Ashok), 6% DRA Brand Fee in the revenue waterfall,
  expressly NOT a partnership at will (Art 3.2), land contributions via registered Contribution Deeds.
- Deed's registered office = Queens Corner; a Prizm Greystone NOC therefore must say
  "establish / shift" its Registered Office to the Scheduled Premises (registered-office change).

## Verification
- Pre-delivery string checks (cheap, catches the wrong-beneficiary bug): python-docx re-extract
  and assert beneficiary present / prior firm absent / issuer identifiers / clause letters / PIDs.
- Render QA without LibreOffice: upload docx to Drive → copy as Google Doc
  (mimeType application/vnd.google-apps.document) → export PDF → pdftoppm -r 110 PNG →
  vision_analyze each page. Clean up temp Drive files after export.

## Mirroring a USER'S OWN manual edits into a sibling NOC (2026-09-18)

NDR often edits the FIRST NOC himself in the Google Doc (deleting paragraphs he doesn't
want) and then asks for the sibling to "look exactly like" it. Do NOT guess what he
removed — download his edited version and diff it structurally.

Pattern that worked (R3N NOC edited by NDR → mirror into DRA KAAJ NOC):
1. Download both .docx from Drive (`files().get_media`) and compare paragraphs.
2. He had deleted two mid-document paragraphs (the O3 lease-chain para and the "rentals
   duly paid" para) — leaving them out of the sibling is the whole point of the request.
3. He also EXPECTED a bullet that the sibling lacked ("Registration of the Firm with the
   Registrar of Firms") — mirroring means adding, not only deleting. Check bullet lists
   line-by-line across both, in order.
4. Flag any remaining difference you deliberately kept (e.g. the sibling's "earlier known
   as …" + Reg No, which identify the beneficiary firm) rather than silently normalising it.

## Re-dating an existing document to a new date (NDR, 2026-09-18)

"Bring all of the dates to today" / "the agreements are dated today" for documents already
on Drive. Rules:
- Change the **header Date line AND the signature-block Date** — he wants "everything" to
  match; a mismatched pair (e.g. header 28.07.2026 vs signature 24.06.2026) is exactly the
  defect this request is fixing.
- Change ONLY the document's own dates. Leave embedded FACT dates alone — the firm's
  registration date (`Reg No. SJN-F823-2023-24 dated 18.11.2023`) must survive untouched.
  Say so explicitly in the delivery note so he can see it wasn't missed.
- Match the document's existing numeric format (`18.09.2026`), don't expand to
  "Friday, 18th September 2026" unless asked. Offer the long form as an option.
- These NOCs live as **.docx on Drive, not native Google Docs** — the Docs API returns
  HTTP 400 "operation is not supported for this document. The document must not be an
  Office file." Edit the OOXML in place (unzip → replace in `word/document.xml` →
  rezip → `drive.files().update(fileId=…, media_body=…)`) to keep the same file id, link
  and version history. See `productivity/gws-automation` for the full upload checklist.
- Before editing, scan EVERY zip part (not just document.xml) for date tokens and report
  anything else you find; assert the old date string is gone after patching.

## Never leave the signature block blank (NDR, 2026-09-18)

Owner-issued NOCs went out with `Mobile No.: __________________` and he immediately asked
for the number to be filled. For a known landlord/owner, fill **Mobile No.** with their
confirmed contact (`+91 …` form) without being asked, and fill the issuer's name and
"Designation: Owner". Only the physical signature stays blank.

- Remove any leftover placeholder text at the same time (e.g. a bullet ending
  `(ABC and other official purposes)`) and flag it — NDR does not want unfilled
  placeholders reaching the Registrar.
- Consequence to flag when the enclosure clause says proof of ownership is "the up-to-date
  tax paid receipt **standing in my name**": the actual tax receipt must be obtained and
  attached. Say so as an action item; don't let the NOC ship without the receipt on file.