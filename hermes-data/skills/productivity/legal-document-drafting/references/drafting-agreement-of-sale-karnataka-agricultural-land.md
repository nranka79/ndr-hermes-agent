# Drafting an Agreement of Sale — Karnataka Agricultural Land

## When to Use

When the user asks you to draft an **Agreement of Sale / Agreement to Sell** for an agricultural land purchase in Karnataka, with a complete title flow extracted from existing sale deeds and a conditions-precedent clause referencing a pending documents requisition list.

## Required Inputs

1. **Latest Sale Deed** — The most recent registered sale deed showing who currently holds title. Need: date, document number, parties, consideration, property schedule.
2. **Earlier title deeds** — Earlier deeds in the chain (older the better) to reconstruct the complete title flow from grant/earliest record.
3. **Pending Documents Requisition List** — A .docx or PDF list of documents the legal counsel requires the vendor to produce (index of lands, RTCs, ECs, family trees, phodi, mutation registers, tax receipts, etc.).
4. **Drive Folder** — Often the user provides a shared Drive folder containing 10-30 title documents (sale deeds, mutations, ECs, RTCs, phodi, release deeds, partition deeds, etc.).

## Workflow

### Step 1: Download All Documents from Drive

```python
drive = build_service('drive', 'v3', service_name='google')
results = drive.files().list(
    q=f"'{folder_id}' in parents",
    pageSize=200, fields='files(id, name, mimeType)',
    orderBy='name'
).execute()
for f in results.get('files', []):
    r = drive.files().get_media(fileId=f['id'])
    with open(local_path, 'wb') as fout:
        fout.write(r.execute())
```

### Step 2: Read What's Readable

**For .docx files:** Use `/opt/hermes/.venv/bin/python3` with `python-docx`.
**For text-based PDFs:** Use `/opt/hermes/.venv/bin/python3` with `pymupdf`.
**For scanned/image PDFs:** Convert to 300 DPI PNGs, then use either:
  - `pytesseract.image_to_string()` for quick bulk OCR
  - `vision_analyze()` for high-quality per-page English text extraction (preferred for key deed pages)

### Step 3: Reconstruct Title Flow

Build a chronological table:

| # | Date | Transaction | From → To | Document Ref | Consideration |

Key entries to identify in every sale deed:
- **Page 1**: Vendor(s) — names, ages, fathers' names, addresses, Aadhar
- **Page 1**: Purchaser(s) — names, ages, fathers' names, addresses
- **WHEREAS/Recitals section**: Chain of previous sale deeds referenced (earlier doc numbers, dates)
- **Pages 5-7**: Sale consideration, payment mode (cheque/DD numbers, bank, date)
- **Property Schedule**: Boundaries (N/E/S/W), survey numbers, extent
- **Last pages**: Signatures, witnesses, notary

### Step 4: Draft the Agreement

Sections to include:

| Section | Content |
|---------|---------|
| I. Schedule Property | Survey numbers, extent, village, hobli, taluk, district, boundaries |
| II. Title Flow | Chronological chain from earliest record to current vendor |
| III. Revenue Records | RTC, IL&RR, EC, mutation, tax receipts status |
| IV. Sale Consideration | Table with advance/earnest money + balance payment |
| V. Conditions Precedent | A: Pending documents list (numbered table from requisition list) B: Additional compliances (khata, taxes, 11E sketch, mutation) |
| VI. Procedure | Documents furnished → Legal DD → Public Notice → Clear Title → Execution |
| VII. Validity | 9 months from signing |
| VIII. Representations & Warranties | Standard vendor covenants |
| IX. Default / Termination | Both sides (vendor default + purchaser default) |
| X. Dispute Resolution | Arbitration + Bengaluru jurisdiction |
| XI. Possession | Only on registered sale deed + full payment |

### Key Clauses (mandatory per user instruction)

1. **Condition Precedent (Section V):** All pending requisition items must be furnished to PURCHASER's legal counsel BEFORE execution. Sub-clauses for each category.
2. **Legal Due Diligence:** Must include publishing a Public Notice in local newspaper calling for claims/objections.
3. **Clear Title Condition:** Sale deed executed ONLY after DD completion AND public notice period with no adverse claims.
4. **Vendor Obligations:** Complete title flow, update revenue records, transfer khatha, pay taxes up-to-date (including 2026-27), furnish 11E sketch/akarbhand.
5. **9-Month Validity:** Fixed — not negotiable per user's standing instruction.
6. **Placeholders:** Leave blank fields for vendor names, purchaser name, sale consideration, earnest money, stamp duty sharing. Mark clearly.

### Pitfalls

- **Registered Indian deeds are scanned images.** pymupdf/pdftotext return 0 text. Use pdftoppm + vision_analyze always.
- **Kannada-only pages.** The 2011 and earlier deeds may be entirely in Kannada — you won't get names from OCR. Use vision_analyze with specific questions ("Read the vendor name in English letters").
- **The "Partition Deed" label is misleading.** The 2023 RMN-1-02893 document is actually a Partition/Relinquishment Deed dissolving a partnership, not a pure sale. Its recitals mention previous sale deeds and agreements.
- **Document filenames may mislabel document type.** Always confirm by page 1 text, not the filename.
- **Mutation records (MR-Hxx)** validate the khatha transfer but don't prove title — they are revenue records, not title documents.
- **E-Stamp pages** show who purchased the stamp paper. Cross-reference the "Purchased by" name with the actual deed parties — an e-Stamp for "Affidavit" may belong to an ancillary document, not the main sale deed.
- **Public Notice cost.** Inform the user that a public notice publication costs approx. Rs.5,000-10,000 (to be borne by vendor or split as negotiated).

## Example: Sy. No. 302, Lakshmipura, Ramanagara (Jul 2026)

See the v3 draft (`20260708_Agreement_of_Sale_Sy302_Lakshmipura_v3_CompleteTitleFlow` on Google Drive) for a complete 19-step title flow from historical grants through 2024.

Key documents found in that folder:
| Document | Key Data |
|---|---|
| 2011 Sale Deed (02883/2011) | Rambilas Chowdhary chain, Rs.12,75,000 |
| 2016 Sale Deed (06660/2016) | Myna Batavia → H. Mahadev |
| 2020 Sale Deed (04889/2020) | H. Mahadev → Eco Town Estates |
| 2023 Partition Deed (02893/2023) | Eco Town Estates → Individual partners |
| 2024 Sale Deed (07372/2024) | Eco Town partners → Current vendors, Rs.85,00,000 |
| 2000-2026 RTC | Continuous RTC records from 2000 |
| 1975-2026 EC | 41-year encumbrance certificate |