# Form 43J / Rule 43 — Karnataka Revenue Document Search

## What is Form 43J?

**Form 43J** (under **Rule 43** of the Karnataka Land Revenue Rules) is a revenue document that records transfers, incorporations, and mutations in land records. It is NOT the same as:

| Document Type | Form/Reference | Purpose | Key Difference |
|---------------|---------------|---------|----------------|
| **Form 43J** | Rule 43 | Transfer/incorporation tracking, mutation/khata change applications | Tabular format, lists survey numbers, areas, parties, registration details |
| **RTC / Pahani Patrika** | Form 16 | Record of Rights, Tenancy & Crops | Multi-year extract, shows current ownership/tenancy per agricultural year |
| **Mutation Register** | Form 11 (Rule 46) | Master ledger of all mutations/changes | Sequential entries of ownership changes, NOT an extract of current status |

## Visual Identification

- **Form 43J**: Landscape or portrait tabular format (old documents may be landscape, newer ones portrait). Kannada header "ಫಾರ್ಮ್ 43ಜೆ" (Form 43J) or reference to Rule 43. Columns for survey number, area, parties, registration details.
- **Old RTC**: Tabular, each row = one agricultural year. Kannada title "ರೆಕಾರ್ಡ್ ಆಫ್ ರೈಟ್ಸ್ ಗಣಿ ಮತ್ತು ಪಹಣಿ ಪತ್ರಿಕೆ". Columns for year, sub-division, area, holder.
- **Mutation Register**: Form 11, reference to Rule 46 ("46ನೇ ನಿಯಮವನ್ನು ನೋಡಿ"). Columns: serial no, document reference, nature of right, survey no, dates.

## Search Strategy

When searching for a specific revenue document like Form 43J:

### 1. Search All Drive Accounts

Don't just search the primary DRAAS account. Also check:
- **ndr@draas.com** (google-draas) — primary business account
- **ndr@ahfl.in** (google-ahfl) — AHFL/Stelo related documents
- **nishantranka@gmail.com** (google-gmail) — personal documents

### 2. Use Multiple Search Query Patterns

| Pattern | Example Query | Best For |
|---------|--------------|----------|
| **Direct form number** | `name contains '43J' or name contains '43j'` | Finding files named after the form |
| **Full text content** | `fullText contains '43J' or fullText contains 'Form 43'` | Finding mentions inside PDFs/Google Docs |
| **Document type keywords** | `fullText contains 'RTC' and (fullText contains 'tenancy' or fullText contains 'crop')` | Finding revenue documents by type |
| **Location-based** | `fullText contains 'Gopasandra' or fullText contains 'Anekal'` | Finding by village/taluk |
| **File name patterns** | `name contains '43' or name contains 'RTC' or name contains 'mutation'` | Catching documents with form numbers in filename |

### 3. Check Inside Multi-Page PDFs

Form 43J pages can be embedded **inside** larger PDFs. A file named "RTC 2002 to 2024.pdf" may contain RTC extracts PLUS Form 43J pages. Always examine the first few pages of candidate PDFs via vision analysis, even if the filename suggests a different document type.

### 4. Use Sub-Agents for Parallel Vision Analysis

For scanned PDFs (no text layer):
1. Convert PDF pages to PNG images: `pdftoppm -png -f 1 -l 3 -r 150 input.pdf output_prefix`
2. Use `delegate_task` with multiple sub-agents to analyze different files in parallel
3. Each sub-agent uses `vision_analyze` to read the scanned image
4. If Kannada text is detected, use `call_openrouter_model` with Gemini 2.5 Flash for translation

### 5. Known Kannada OCR Limitations

- Standard OCR (Tesseract) works poorly on Kannada text in scanned documents
- `vision_analyze` with OCR mode may produce garbled output for Kannada
- Always use `call_openrouter_model` with `google/gemini-2.5-flash` for reliable Kannada→English translation
- The Gemini model can read Kannada text from images AND translate it in one step

## Known Document Location Patterns

### AHFL / Stelo Documents (Dharwad)

AHFL documents for Ranka Stelo project are typically found in:
- **DHARWAD PROJECT DOCUMENTS** folder (owned by kulkarni@ahfl.in, accessible via ndr@draas.com)
- **RANKA STELO > AHFL** folder (owned by narayan@ahfl.in)
- **Stelo** folder under Current Properties (owned by ndr@draas.com)
- Recently uploaded files may be in **"Ahfl Master Folder"** with AHFL FILE 1-11 sub-folders, uploaded by Bharat (sales1.blr@draas.com)

### Document Discovery via Gmail

- Use Gmail API: `service.users().messages().list(userId='me', q='query').execute()`
- Gmail can find references to forms/documents even when they weren't attached as files
- Check all three accounts (DRAAS, AHFL, personal)

## File Sharing with External Contacts

When sharing found documents with external parties (lawyers, consultants):
1. Share via Google Drive permissions: `drive.permissions().create(fileId=..., body={'type': 'user', 'role': 'reader', 'emailAddress': email, 'expirationTime': expiry})`
2. Set 1-week expiry for viewer access
3. Send the Drive links via WhatsApp (preferred) or email draft

## Verified Example (Jul 2026)

**Search target:** Form 43J / Rule 43 extract for Gunjur, Gopasandra, Bandal villages

**Results found:**
1. ✅ Form 43J — Gopasandra, Anekal Taluk (in `2002 to 2024 rtc SyNo 93.pdf`, page 1) — Transfer/incorporation tracking sheet, Survey 93
2. ✅ Form 43J — Bandal, Ilakal Taluk, Bagalakote Dist (in `rtc 2005 to 2015 SyNo.93.2.pdf`, page 1) — Mutation/khata application, Survey 93/2
3. ❌ Gunjur — No Form 43J found, only standard RTC (Form 16)

**What also turned up but was NOT Form 43J:**
- `Gunjur Sy No 38 - RTC from 1969-70 to 2002-03.pdf` — Standard RTC/Form 16 (Pahani Patrika), not Form 43J
- `Sy No 38 MR 4-43-44.pdf` — Form 11 Mutation Register (Rule 46). "43-44" = Financial Year 1943-44, NOT Form 43J

**Vault token access** — When the session user differs from the document owner (Nishant's token under canonical_uid `ndr-[REDACTED-TID]`), access Google APIs via terminal() with the venv Python: `cd /opt/hermes && /opt/hermes/.venv/bin/python` with `GWS_VAULT_SOCKET` available. The execute_code sandbox does NOT have vault access.
