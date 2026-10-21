# BBMP Commencement Forms — Annexure VIII & IX

Two statutory forms required under Bye-law 5.2(i) of the BBMP Building Bye-Laws,
filed at different stages of construction. Every BBMP-licensed project needs
these.

## The Two Forms

| Form | Annexure | When Filed | Certifies | Filed By |
|------|----------|-----------|-----------|----------|
| **Intimation of Commencement** | VIII | Before construction starts (earth work begins) | Builder intends to start construction per sanctioned plan | Owner + registered Architect/Engineer |
| **Commencement Certificate Application** | IX | After **plinth level** is reached | Building constructed up to plinth as per sanctioned plan | Owner + registered Architect/Engineer/Supervisor |

Newer BDA/GBA-sourced blank forms say "Application for Plinth Certificate (U/s 239 of The Greater Bengaluru Governance Act, 2024)" — the Annexure IX under the 2024 Act. Same fields, new statute reference.

## Relationship

1. **Annexure VIII** is filed first (intimation that work is about to begin).
   This is the form that triggers the 2-year commencement deadline clock from
   the plan sanction date.
2. **Annexure IX** is filed weeks/months later after the plinth is concreted.
   This is a formal certification that the building matches the sanctioned plan
   at the ground / plinth stage — deviations caught here are much cheaper to fix.
3. Some projects file VIII at plan sanction issuance and IX when actual
   earthwork starts — check the project's specific timeline.

## Common Fields (Both Forms)

| Field | Source |
|-------|--------|
| Zone | Mahadevapura (for BECC/East), West, South, etc. — from the LP prefix |
| Property No. | BBMP PID (from e-Khata / plan sanction) |
| Plot No. | From plan sanction / layout plan |
| Ward No. | From plan sanction |
| Locality / Street | Full address: layout name, village, hobli, taluk |
| LP No. | Plan sanction number e.g. `GBA/BECC/0540/25-26` |
| LP Date | From plan sanction date |
| Owner | Promoter entity / director's name and designation |
| Architect | Name, firm, address, COA registration number |

## Where Each Value Lives (Ranka Amber, verified Sep 2026)

- **Address / sanction basics** — "20260608 Ranka Amber Project Details Letter - Updated.docx" (text layer; quickest). Plot 1-B · Katha 4/124 · BBMP PID 7057785976 · D'Silva Layout, Pattandur Agrahara Village, K.R. Puram Hobli, Bengaluru East Taluk – 560 066.
- **Zone / Ward / Project No / Plot / City Survey / Khata** — NOT on the letter; read the **AutoDCR sanction plan text layer** with `pdftotext -layout` (the drawing has a text layer even though it looks like a plan): `Project No: GBA/BECC/0540/25-26`, `Authority: Bengaluru East City Corporation`, `Zone: Mahadevapura`, `Ward: Ward 083`, `Plot/Sub Plot No.: PLOT NO:1-B`, `City Survey No.: 4/124`, `Khata No. (As per Khata Extract): 7057785976`, `Land Use Zone: Industrial-I(H) (Hi-Tech)`, Planning District 315-Whitefield. The `GBA/BECC/` prefix itself = Bengaluru East City Corporation. **Never web-guess the ward number — it is in the plan text layer.**
- **Architect** — "Ranka Amber - Form 2 - Architect Certificate (Scan).pdf" in the RERA scanned folder (OCR via vision_analyze): **Anjali Mandhyan, Registered Architect, COA No. CA/2018/100260**; the certificate explicitly cites "Sanctioned Drawing No. GBA/BECC/0540/25-26".
- **Engineer / Supervisor** — "20260725_RankaAmber_Engineer_Certificate.pdf" (Construction Cost Abstract): **Loganathan M, Consulting Civil Engineer, License No. BCCL/BL-3.6/E-0293/24-25, SLVS DESIGN CONSULTANTS LLP, Bangalore**. Note: "Engineers Registration certificate - Attested.pdf" in the same folder is S. Vinay Prasad (KDTCP RE-GR II 33/2024 — Tamil Nadu registration) — likely NOT the BBMP on-record engineer; verify before using.
- **Owner / promoter block** — DRA REALTY PRIVATE LIMITED, 201A/202BA, Queens Corner, No. 3, Queens Road, Bengaluru – 560 001; CIN U70100KA2011PTC058105; signatory Nishant Ranka, Director.

## Workflow for a New Project

1. **Collect from the project data map:** BBMP PID, Plot No., Ward No.,
   locality/address, LP No. and date, promoter details, architect details.
   The `ranka-amber-data-map.md` reference has the full structure.
2. **Create Annexure VIII** — fill the owner and architect sections.
   Owner signs at the "Commencement Date" (project start date from SIS).
   Architect certifies their supervision.
3. **Create Annexure IX** — same fields as VIII but adds the plinth-level
   certification paragraph. Owner signs at approximate plinth completion date.
4. **Deliver two ways (either is fine):**
   - **Editable .docx** via python-docx (Times New Roman 12pt). Fields not yet
     known go in `[bracketed placeholders]`.
   - **In-place fill of a shared blank Google Doc via the Docs API** — the
     preferred path when the user hands you the BBMP blank form as a GDoc link
     and says "update this form" (Sep 2026 session). Keeps the SAME link. See
     the technique below.

## In-Place Fill of a Blank Google Doc (Docs API) — Proven Recipe

Used to fill the shared `ANNEXURE IX CC APLICATION` GDoc for Ranka Amber without
changing the link. Works for ANY government/letter template GDoc with dotted
blanks.

1. `docs.documents().get()` → concatenate every `textRun.content` in order
   (paragraph runs are contiguous; document index = offset in the string + 1).
   Trailing `\n` inside textRun content is normal.
2. For each blank: locate the phrase before the dots (e.g. `"Ward No"`), then
   scan from `index_of_phrase + len(phrase)`:
   - **Skip leading spaces first** (most blanks are `"Phrase ….…"` with one space).
   - Blanks are runs of `…` (U+2026) — the form's dotted lines. Some are split
     by `.` or grouped with spaces (`"….…….…"` → groups). Assert the segment is
     all dots before touching it; delete that span and `insertText` the fill.
   - For `_`-delimited lines (the Zone line `"________________________ Zone"`),
     scan `_` instead.
3. **Order every batch request by DESCENDING start index.** Docs API applies
   requests in order on the evolving document; higher-index operations never
   shift lower indices, so descending order is safe with original indices.
   Each edit = `deleteContentRange(span)` then `insertText(fill, at span start)`.
4. **Cleanup pass:** residual dot/period runs remain between fills (the form's
   dots come in split groups — e.g. after filling Plot No there was still
   `".…………."` before Ward No). Between known anchor phrases, if the segment is
   all dots/periods/spaces, delete → single space. Then `replaceAllText('  ', ' ')`
   (repeat twice) to collapse double spaces from fill+template spacing.
5. Leave the signature lines, Name/Address block lines, Registration No,
   Place/Date lines dotted/blank — those are physically signed. Pre-fill the
   Name lines only if the owner/architect names are certain.
6. Verify by re-reading the doc and printing the body text; check every fill
   landed and no stray dots sit mid-sentence.

## Ranka Amber Worked Example (Sep 2026 fill)

| Field | Value |
|---|---|
| Zone | Bengaluru East City Corporation (Mahadevapura Zone) |
| Property No. | 1-B (BBMP PID: 7057785976) |
| Plot No. | 1-B |
| Ward No. | 083 |
| Locality | D'Silva Layout, Pattandur Agrahara Village, Whitefield Main Road, Bengaluru – 560 066 |
| LP No. | GBA/BECC/0540/25-26 |
| LP Date | **07-05-2026** per "AMBER SANCTION 07.05.2026.pdf"; plan generation stamp says 18 May 2026 — flag for confirmation (earlier reference said 18 May) |
| Owner | M/S DRA Realty Pvt Ltd (through Director Mr. Nishant Ranka) — 201A/202BA Queens Corner, Queens Road |
| Architect | **Anjali Mandhyan, COA No. CA/2018/100260** (updated Sep 2026 — was "awaited" in Jun 2026) |
| Engineer | **Loganathan M, BCCL/BL-3.6/E-0293/24-25, SLVS Design Consultants LLP** |
| Building | Erection of a new residential apartment building (ST + GF + 3 floors, 20 units 3BHK) |

## Pitfalls

- **Architect's COA registration number** is often pending at form filing time.
  Fill as `[COA Reg. No. — to be filled]` and have the architect insert before
  signing. (For Ranka Amber it IS now known: CA/2018/100260 — update stale
  "awaited" notes.)
- **Annexure IX needs a DIFFERENT date than VIII** — VIII = start date, IX = plinth
  completion date. Don't copy the same date.
- **Form IX requires engineer's OR architect's signature**, not both. Use the
  architect when the structural consultant is at a different firm.
- **Times New Roman 12pt** is the expected font for BBMP forms. Do NOT use Calibri,
  Arial, or other modern fonts — they flag as non-standard on submission.
- **The Engineer's license/reg number** for Annexure IX (Engineer column) is
  typically the structural consultant's license, not the site supervisor's. Check
  who is registered with BBMP for the project.
- **Sanction date conflicts:** filename "AMBER SANCTION 07.05.2026.pdf" vs plan
  "Date: 18 May 2026 11:05:47" (AutoDCR generation stamp). Always cross-check the
  sanction letter before committing a date to a statutory form.
- **Docs API blank detection:** spans can be empty if you forget the leading-space
  skip or scan `…` when the run is `_` (or vice versa). Assert segment content
  before batchUpdate; an empty `deleteContentRange` is a hard 400.
- **Shortcut files on Drive** (e.g. BESCOM sanction letter) may 404 from the
  session token even when the shortcut lists in the folder — resolve
  `shortcutDetails.targetId` and if `files().get` on the target 404s, ask the user
  to share the source file; don't block the form on it.