# Agreement of Sale — Drafted from Prior Sale Deed + Requisition List as CP

## When to Use

When the user provides (a) a prior registered **Sale Deed** (scanned PDF) and (b) a **Requisition List** from legal due diligence, and asks you to draft a fresh **Agreement of Sale** embedding the requisition items as **Conditions Precedent**.

This is a DRAAS land acquisition pattern: the purchaser's legal team reviews title documents, issues a requisition list of missing/pending documents, and the Agreement of Sale makes those a condition precedent to closing.

## The Workflow

### Step 1 — Extract Both Source Documents

| Document Type | Tool | Notes |
|---|---|---|
| **Scanned PDF Sale Deed** (image-based) | pymupdf → render 300 DPI PNG per page → pytesseract OCR | Install: `uv pip install pymupdf pytesseract pillow`. Sale deeds from Karnataka SRO are image-based, not text-selectable. |
| **DOCX Requisition List** | python-docx | Extract paragraphs AND tables. Requisition lists are often formatted as tables with Sl.No, Particulars, Client Comments columns. |

### Step 2 — Extract Key Data Points from Sale Deed

From the OCR output, extract:

- **Date of Deed & Registration No.** (e.g., "04-11-2020, RMN-1-04889-2020-21")
- **VENDOR** (seller) — name, age, father's name, address, Aadhar/PAN
- **PURCHASER(S)** — individual names or entity name + partners/directors
- **Schedule Property** — Old Sy.No, New Sy.No, extent, village, hobli, taluk, district
- **Boundaries** — East/West/North/South
- **Sale Consideration** — amount in words and figures
- **Title Recitals** — how the vendor acquired the property (prior sale deeds, mutation, khatha)

### Step 3 — Reconstruct the Title Flow Chain

Link the sequence:
1. Original holder → first transferee (via Sale Deed A, Doc No. X)
2. First transferee → second transferee (via Sale Deed B, Doc No. Y)
3. ... → current VENDOR/S

Leave the last link from the Sale Deed vendor to the current VENDOR/S as an open section if that devolution is not documented.

### Step 4 — Structure the Agreement of Sale

Sections required:

| Section | Content |
|---|---|
| **A — Schedule Property** | Boundaries, survey, extent, taluk/district |
| **B — Title Flow** | Full chain from earliest known title to current vendor |
| **C — Sale Consideration** | Amount + payment tranches (blank for filling) |
| **D — Conditions Precedent** | ALL items from the requisition list, enumerated; PLUS additional vendor obligations (khata transfer, revenue records, 11E sketch, tax paid, EC) |
| **E — Conditions Subsequent** | Furnishing docs → legal due diligence → public notice → claims period → execution only after clearance |
| **F — Validity** | 9 months from signing (standard DRAAS term) |
| **G — Default & Termination** | Vendor default (refund + interest / specific performance); Purchaser default (forfeiture) |
| **H — Representations & Warranties** | Clear title, no encumbrances, no litigation, indemnity |

### Step 5 — Embedded Requisition List Treatment

Every item from the requisition list should appear as a numbered row in Section D. The "Client Comments" column is typically empty — the Agreement of Sale converts these from observations into obligations.

**Format:** Table or numbered list with Sl.No, Document Required descriptions.

### Key Terms to Enforce (per DRAAS standard)

- **Condition Precedent:** All documents must be furnished to PURCHASER's legal counsel
- **Legal Due Diligence:** Counsel to verify title + publish public notice in local newspaper
- **Clear Title Condition:** Sale deed executed ONLY after due diligence clearance AND public notice period without adverse claims
- **Validity:** **9 months** from signing
- **Vendor Obligations:** Complete title flow, revenue records (RTC), khatha transfer, up-to-date tax paid (2026-27), 11E sketch / Akarbhand, non-encumbrance certificate from 01-04-1975 to date

## Pitfalls

1. **Kannada text in scanned deed:** Karnataka SRO deeds have Kannada boilerplate on every page (stamp duty, registration details). OCR will produce garbled Kannada — ignore it. Focus OCR on the English operative portions.
2. **Boundary mismatch:** The requisition list may reference slightly different boundaries than the sale deed. Use the sale deed boundaries as primary and note any discrepancies.
3. **Missing intermediate title link:** The Sale Deed from 2020 may show Eco Town Estates as purchaser, but the current VENDOR/S are different. Document this gap and mark it for the user to fill in.
4. **Leave amounts blank:** Sale consideration and advance/earnest money should be left as blanks — the Agreement of Sale is for a new transaction with different parties.

## Worked Example (July 2026 — Sy. No. 302, Lakshmipura, Ramanagara)

Source documents:
- Sale Deed RMN-1-04889-2020-21 dated 04-11-2020 (vendor: H. Mahadev → purchaser: Eco Town Estates, 3 partners)
- Requisition List II dated 01-07-2026 (36 items)

Title Flow extracted:
- Myna Batavia → H. Mahadev (Doc 6660/2016-17, 05-11-2016) → Eco Town Estates (Doc RMN-1-04889-2020, 04-11-2020) → [current VENDOR/S pending]

Requisition List had 36 items including: Index of Lands, RTCs, death certs, family trees, GPA clarifications, mortgage records, phodi, EC from 1975, atlas sketch, tax receipts, hissa tippani, village map, survey map, pakka book, grant certificate, nil tenancy certificate, release deed clarification, bank mortgage status, litigation status.

Draft output saved at: `/data/hermes/document_cache/Draft_Agreement_of_Sale_Sy302_Ramanagara.md`