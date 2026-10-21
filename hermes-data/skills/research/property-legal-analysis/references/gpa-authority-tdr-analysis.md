# GPA / Power of Attorney — Authority Analysis for TDR/DRC Applications

When the user asks "does the GPA from the landowners cover applying for TDR/DRC?" or "can the developer/GPA holder sign the TDR affidavit and Form IV?" — use this clause-by-clause analysis methodology.

## Trigger

- "Check whether the GPA covers TDR applications"
- "Can I sign the affidavit and Form IV as GPA holder?"
- "Does the developer have authority to apply for DRC?"
- Any question about the scope of a GPA/POA against a specific statutory proceeding

## Workflow

### 1. Find the Operative GPA Document

Not every GPA in the Drive is the right one. The key document is the general power of attorney (GPA) executed BY the landowners IN FAVOUR OF the developer/attorney. Look for:

- `GPA From LO ALL to DRA PROJECTS PVT LTD` or similar naming pattern
- Often dated concurrently with the JDA (e.g., 07.02.2014 for the Northstar JDA)
- Check for copies at different paths — exclude obviously unrelated ones (other projects, other villages)

### 2. OCR the Scanned GPA

Most historical GPAs are scanned PDFs with 20+ pages and NO text layer:

```bash
cd /tmp && mkdir -p gpa_ocr
pdftoppm -r 300 -gray input.pdf gpa_ocr/p
for f in gpa_ocr/p-*.pgm; do
  tesseract "$f" "${f%.pgm}" -l eng --psm 6 2>/dev/null
done
cat gpa_ocr/p-*.txt > gpa_all.txt
```

Use 300 DPI — legal font in registered deeds is small (10-11pt) at the edges of scanned pages.

### 3. Read the Powers Clause-by-Clause

Identify these four tiers of authority:

**Tier A — Express KTCP-specific clauses (strongest)**
Look for clauses that name "authorities under the Karnataka Town and Country Planning Act" or "the Karnataka Town and Country Planning Act, 1961" or similar. These explicitly include the TDR regime under Sec 14-B.

**Tier B — Land Acquisition / Compensation clauses**
Clauses covering "appear before the Land Acquisition Officer", "acquisition proceedings", "sign and execute documents in respect of acquisition". TDR/DRC is a compensation mechanism for acquired land — these clauses clearly cover the same domain.

**Tier C — Broad statutory authority clauses**
Look for:
- "Sign and submit necessary applications, petitions, memorandum, affidavits, undertakings, documents and other papers and to represent [the owners] before the Revenue Authorities, authorities under the Karnataka Town and Country Planning Act, Bangalore Development Authority… or any other local bodies or statutory authorities, State Government, etc., in connection with all or any matter pertaining to the Schedule Properties"
- "Submit applications, affidavits, statements, returns to the Government of Karnataka and/or authorities under any state or central statute, to obtain necessary clearances, exemptions, sanctions and permissions required under any applicable law"

**Tier D — General/Residual/Incidental clauses (supports the above)**
- Power to "do all such acts and things which are incidental and necessary"
- "To generally do all such acts, deeds and things as may be necessary"
- Ratification clause: owners ratify and confirm whatever the attorney lawfully does

### 4. Map the Clauses to the TDR Regime

| Clause Type | TDR Element Covered |
|---|---|
| KTCP authorities (Tier A/C) | TDR is governed by Sec 14-B KTCP Act 1961 + Karnataka TCP (Benefit of DR) Rules 2016 — the application goes to the Executive Engineer under these rules |
| Land Acquisition Officer (Tier B) | The TDR claim arises because land is acquired for a road by BBMP — land acquisition proceedings are the trigger event |
| Broad statutory authority (Tier C) | Signing and submitting the Form IV, Affidavit, and all supporting documents before the competent authority |
| Incidental/residual (Tier D) | Obtaining the DRC certificate, following up, doing whatever is needed to complete the process |

### 5. Check for Purpose Limitations

The GPA's recitals may say "in respect of developing the Schedule Properties by constructing a Residential Apartment Premises" — this is a purpose limitation that a strict-reading officer could rely on to deny authority for TDR (since TDR isn't construction). Override this by:

- **Addendum/JDA TDR clause**: If the JDA Addendum (even one executed years later) contains a clause allocating TDR benefits between owners and developer (e.g., "owners get 15% of SBUA from additional FAR including TDR"), this is STRONG evidence the parties intended the developer to pursue TDR on behalf of the owners. Cite it.
- **Clause 27/29 (general/ratification)**: These override the purpose limitation in most practical contexts.

### 6. Entity Mismatch Check

**Critical question:** Is the GPA in favour of the same entity that is applying?

The GPA names M/s DRA PROJECTS PRIVATE LIMITED (the company). If the JDA developer rights moved to a different entity (e.g., DRA Ranka Holdings via assignment), and that entity files the TDR claim, there's a gap:
- If filing as "DRA Projects" → GPA covers it ✓
- If filing as "DRA Ranka Holdings" → the GPA is NOT in that entity's name — needs assignment ratification or a fresh GPA

Action: confirm with the user which entity they intend to sign as, and structure the forms accordingly.

### 7. Execution Format for the Forms

Once authority is confirmed, structure the affidavit and Form IV signature blocks:

```
OWNERS: [list of 7 joint landowners]
  acting through their GPA holder
M/s [COMPANY NAME] (per registered GPA dated [DD.MM.YYYY])
  represented by its Director, Mr. [NAME] (Aadhaar No. [XXXX])
--------------------------------------------------------
(Signature — Director, for [COMPANY], as GPA holder)
```

Key elements:
- The GPA is the COMPANY's power, not the director's personal power — sign as company representative
- Include the GPA registration details in the body or as a note (date, SRO, Doc No.)
- Attach a certified copy of the registered GPA as an annexure to the pack
- Use a GPA Cover Page + scan merge via qpdf for the annexure

## Pitfalls

- **GPA recital purpose limitation**: The dominant purpose described in the GPA's recitals may be "development and sale of constructed area" — TDR is inferable via broad clauses but not expressly named. Mitigate by attaching the Addendum's TDR clause as a supporting document.
- **Company vs individual signing**: The GPA names the COMPANY, not a person. The signatory must sign "For [Company], as Director" — not in their personal capacity.
- **Registered GPA required**: The GPA must be registered at the SRO. An unregistered GPA is rarely accepted as authority for registration/submission before statutory authorities.
- **JDA assignment may leave the GPA orphaned**: If the JDA was assigned to a different entity but the GPA wasn't updated, the applying entity may not be the attorney. Check whether a separate GPA assignment deed exists or whether the GPA covers the assignee via a delegation clause.
- **Check the full chain for individual owners**: If a specific owner (e.g., Kankshita, an NRI/OCI) executes through their OWN GPA holder (e.g., father), that GPA chain must also be valid for the TDR application to bind them. Verify: Owner → their GPA holder → developer GPA → application.