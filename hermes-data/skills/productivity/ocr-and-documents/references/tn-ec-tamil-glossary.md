# TN EC (Encumbrance Certificate) — Tamil→English Glossary

Compiled while translating EC for Survey 235, Sevaganapalli (Hozur/Bagalur SRO,
Krishnagiri district), issued 12-Aug-2026, 23 pp / 24 entries. Recurring Tamil
tokens in TN Reginet EC VALUES — the column labels are already English in the
bilingual PDF, so only values (names, boundaries, remarks, extents) need
translation.

## Boundary directions (order in original text: கி, மே, வ, தெ)
- (கி) / கிழக்கு = **East**
- (மே) / மேற்கு = **West**
- (வ) / வடக்கு = **North**
- (தெ) / தெற்கு = **South**
- மத்தியில் = in the middle / within this boundary (often marks the extent clause)
- முழுவதும் / பூரா = entire / full (extent)

## Land & survey terms
- சநெ / ச.எண் / சர்வே எண் = Survey No. (render as "Sy. No.")
- புல எண் = survey / field number
- மனை எண் / பிளாட் எண் = Plot No.
- விவசாய எண் = agricultural plot number
- புறம்போக்கு = poramboke (government waste land)
- வண்டிபாதை = cart track
- மீதிநிலம் = remaining land (e.g. "சநெ 235/2 மீதிநிலம்" = remaining land of Sy. No. 235/2)
- ஏ. / ஏக் / ஏக்கர் = Acre; செண்ட் = cent; ஹெக்டர் = hectare; ச.அடி / சஅடி = sq. ft.
- நிலம் = land; கிராமம் = village; எல்லை = boundary
- விவசாய நிலம் / வேளாண் நிலம் = agricultural land

## Document nature & remarks
- கிரய பத்திரம் = Sale Deed
- சம்மத பத்திரம் = Consent / Ratification deed
- பொதுஅதிகார ஆவணம் = General Power of Attorney document
- வி.ரூ = document (consideration) value; ச.ம.ரூ / மா.ம = market value
  (e.g. "வி.ரூ.53900 ச.ம.ரூ.53935" → Doc value Rs. 53,900; Market value Rs. 53,935)
- 47(அ) / "47(A) Details" block = deficit stamp duty referral under Section
  47-A(1) to the District Revenue Officer (Stamps) / Deputy Collector (Stamps),
  with the collected amount + date

## Party-name notes
- Names often appear Tamil-phonetically in early entries and English for the
  same person in later entries (ஷாரத் ஹெட்ஜ் = Sharath Hedge, பாலகிருஷ்ணரெட்டி =
  Balakrishna Reddy, சியாம் ரெட்டி = Shyam Reddy). Transliterate consistently
  and match across entries.
- (முத.) = **Principal**, (முக.) = **Agent** — suffixes on company/party names
  (e.g. "TIARA REALTY(முத.) DANIEL IVES CLIFFORD(முக.)" = Tiara Realty
  (Principal) — Daniel Ives Clifford (Agent)).
- Keep role markers: (கார்டியன்) = Guardian, (மைனர்) = Minor.
- @ = alias chains (e.g. "நாகராஜு ரெட்டி @ நாகி ரெட்டி @ நாக ரெட்டி" = Nagaraju
  Reddy @ Nagi Reddy @ Naga Reddy) — preserve the aliases, they are identity-critical.

## Format facts (for faithful reproduction)
- Page size **A4 landscape 842×595 pts**; check with `pdfinfo` before rendering.
- Header: govt dept banner, certificate title, metadata table (S.R.O, Date,
  Registration Village, Survey Details, Revenue District/Taluk/Village),
  data-availability period per SRO, search period.
- Transaction table columns: Sr.No | Document No & Year | Date of Execution &
  Date of Presentation & Date of Registration | Nature | Executants | Claimants
  | Vol.No & Page No. Vol/Page is usually "—" (dash) in digital ECs.
- Zone row repeats on the first page: "Zone: Salem | District: ... | S.R.O: ..."
- Each entry is followed by Consideration Value / Market Value / PR Number, then
  one or more Schedule blocks (Property Type, Property Extent, Village & Street,
  Survey No., Plot No., Boundary Details, Schedule Remarks). Entry 19-type
  umbrella deeds (e.g. GPA over a layout) can carry 30+ schedules — enumerate
  them all; don't summarize.
- PR Number field can be truncated in the source PDF ("1701/201…") — keep as-is
  and flag it; do not guess the tail.
- Footer: "Number of Entries: N", disclaimer, helpdesk block (toll-free
  1800 102 5174, helpdesk@tnreginet.net).
