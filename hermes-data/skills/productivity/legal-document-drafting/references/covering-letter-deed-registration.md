# Covering Letter for Deed of Reconstitution Registration

## When to Use

When the user asks you to draft a covering letter addressed to the **District Registrar** accompanying the registration of a **Deed of Reconstitution of Partnership**. This letter is typically requested by the Registrar's office to clarify which properties are being brought into the reconstituted firm vs which properties from the original partnership deed are **not** being contributed.

## Core Structure

A covering letter for reconstitution registration has three logical sections:

### 1. Original Partnership Deed — Properties NOT Being Taken In

List every schedule from the **original partnership deed** that is being **excluded** from the reconstitution. Present in tabular format:

```
Schedule [X] — Properties at [Village Name]
| Item | Survey No. | Village | Extent |
|------|-----------|---------|--------|
| 1    | [Sy No]   | [Village] | [A G] |
```
Include a clear declaration:

> "It is hereby declared that **none of the Schedule Properties mentioned under [Schedule X] of the Original Partnership Deed dated [date]** are being brought into or taken over by the reconstituted Firm."

**Also include the reason** for exclusion — typically: "This is on account of the fact that the title documents of the said properties did not complete the due diligence process as per the requirements of the reconstituted Firm." State this both in the declaration section and in the closing request bullet points.

### 2. Reconstitution Deed — Properties BEING Brought In

List every schedule from the **reconstitution deed** being contributed to the firm. Organise by Schedule letter (A, B, C, etc.) and include for each item:
- Survey Number (old and new)
- Extent (Acres + Guntas)
- Village, Hobli, Taluk, District
- Boundaries (E/W/N/S) — include if the schedule has them
- Agreed Valuation — include if stated in the deed

Format as tables for readability. For deeds with sub-parts (e.g. Part A - Registered Sale Deeds, Part B - Agreement of Sale/GPA), maintain that subdivision.

### 3. Formal Request

A closing paragraph making the actual request:

> "You are therefore requested to kindly register the Deed of Reconstitution of Partnership executed on [date] for [Firm Name] (formerly [Old Firm Name]), Firm No. [Registration No.], in accordance with the applicable provisions of the Indian Partnership Act, 1932 and the Karnataka Stamp Act, 1957."

## Data Sources

| Data | Source | Extraction Method |
|------|--------|------------------|
| Original deed schedules | Scanned/PDF original partnership deed | pdftoppm → tesseract → keyword search for "SCHEDULE", "Item No", "Survey" |
| Reconstitution deed schedules | Google Doc of reconstitution deed | Docs API (Google Doc) — text extraction is clean |
| Execution details (date, parties) | Both deeds | Read preamble/execution block |
| Firm registration number | Reconstitution deed recitals | Recital A (Original Deed reference) |

## OCR Workflow for Scanned Deed Schedules

When the original deed is a scanned PDF (pdftotext returns empty):

```bash
# 1. Convert PDF pages to PNG at 200 DPI
pdftoppm -png -r 200 input_deed.pdf page

# 2. OCR each page with tesseract, searching for schedule sections
for p in page-*.png; do
    text=$(tesseract "$p" stdout 2>/dev/null | head -40)
    if echo "$text" | grep -qi "schedule\|SCHEDULE\|Item No\|survey\|bound"; then
        echo "=== $p ==="
        echo "$text"
    fi
done

# 3. For properties in table format (Survey No. / Extent columns), 
# tesseract usually reads them row by row — check page output
# for the actual columns, as e-stamp and document headers also appear
```

**Known OCR issues on registered deeds:**
- E-stamp certificates at the top of page 1 are OCR'd as document content — ignore them
- Kannada place names may be garbled — compare against the Google Doc version of any later deed
- Table cells without borders may merge adjacent columns — check multiple pages for context
- "Guntas" may appear as "Guntas", "Gunta", or broken across lines

## Property Table Reconstruction

When the schedule is in list/table format (Survey No. → Extent in Guntas), reconstruct it as a clean table:

```
| Village | Survey No. | Extent (Guntas) |
|---------|-----------|----------------|
```

If boundaries (E/W/N/S) are described in the deed for each item, include them in a separate column or list them under each item in the covering letter — the Registrar expects the same level of detail as the original deed.

## Firm Registration Number Verification

After drafting the covering letter, the user may ask to **verify the firm registration number** against the official acknowledgement document.

### Workflow

1. **Find the acknowledgement PDF** — Look in the same Drive folder for files named like `Ack *Firm*.pdf`, `Ack*Registration*.pdf`, or similar
2. **Download and OCR** — These are typically single-page scanned PDFs. Use the standard scanned-PDF workflow:
   ```bash
   pdftoppm -png -r 200 ack_deed.pdf ack_page
   tesseract ack_page-1.png stdout
   ```
3. **Extract and verify these fields:**

   | Letter Field | Verify Against Acknowledgement |
   |-------------|-------------------------------|
   | Firm Number | `Firm Number : SJN-XXX-XXXX-XX` — most critical field |
   | Date of Registration | `Date Of Registration : 18 Nov 2023` |
   | Office | `Office of the Registration of Firms : SHIVAJINAGAR` — match to jurisdictional office |
   | Firm Name | `Name of Firm : DRA MUTHANALLUR LAND PARTNERS` |

4. **The acknowledgement format** (Form C under Rule 3(5) of the Indian Partnership Act):
   - Header: Government of Karnataka — Acknowledgement of Registration of Firm
   - Firm Number + Date Of Registration on top
   - Office name below
   - Registrar's acknowledgement paragraph (Section 58(1) of the Partnership Act)
   - Firm Name + Address
   - Designation: Registrar of Firms, [Office Name]

5. **Confirm to user** — If all fields match, report which fields were verified and show the matching values.

## Key Pitfalls

- **The original deed may be a scanned PDF** — never assume pdftotext will work. Always check text length; if < 100 chars, use pdftoppm + tesseract.
- **Page numbering in scanned PDFs** may not match the logical document structure. E-stamp pages and definition sections appear before schedules — continue through all pages.
- **Two sets of schedules to compare**: Covering letters compare properties FROM (old deed) vs properties TO (new deed). Make sure you don't mix them up.
- **Total extent reconciliation** — add up the individual items and state the total in the letter. If the deed states a total (e.g. "approximately 40 Acres"), include both the stated and the computed total.
- **Registrar's office expects the letter to be signed by all continuing partners** of the reconstituted firm. Include signature blocks for each partner.
- **Verify firm reg number from the acknowledgement, not the deed recitals** — The recitals in the reconstitution deed (Recital A) *do* quote the original firm number, but the user may want independent verification from the official acknowledgement PDF. Don't assume the deed is correct — always cross-check when asked.
- **State the reason for exclusion.** When original properties are excluded, add the reason (e.g. title documents did not complete due diligence per firm requirements). This pre-empts the Registrar's question of why original properties are missing.
- **Keep property descriptions concise — no background narrative.** When describing each contributing party's properties, just state: "These properties belong to [Party Name] and are being contributed to the reconstituted Firm." Do NOT add detailed context about how they acquired the property (dissolution of prior entity, partition deed backstory, acquisition cost, payment chain). The user (Nishant) explicitly rejects this level of detail in covering letters — it makes the document needlessly verbose. The background belongs in the main deed's recitals, not in the covering letter.
