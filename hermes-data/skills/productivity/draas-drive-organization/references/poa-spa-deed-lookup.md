# POA / SPA / GPA deed lookup in DRA Drive (verified 2026-09-23)

Trigger: "did we ever give X a power of attorney / SPA from <entity>?", "find the
signed SPA for <person>", "give me the link to the signed POA". Worked case:
Bharat Hawaldar SPAs from DRA Realty (SPA No 503/2024, SPA 26-Sep-2024 Anbu+Bharat,
SPA No 675 GNR-4-00675-2025-26) + the Ranka Amber GPA direction check.

## Drive query set (google-draas primary, then ahfl + gmail)

- `name contains 'power of attorney'`, `name contains 'POA'`, `name contains 'GPA'`, `name contains 'attorney'`, `name contains 'Special'`
- Person sweep: `fullText contains 'Hawaldar'` (Drive's index OCRs scanned deed PDFs, so fullText finds names INSIDE registered scans)
- Combined project×person: `fullText contains 'Amber' and fullText contains 'Hawaldar'` — narrows straight to the relevant deed
- Project enumeration: `name contains 'Amber'`
- Always pass `supportsAllDrives=True, includeItemsFromAllDrives=True`; signed deeds live in folders like "SPA and GPA Folder"

## Verify each candidate — downloads + text extraction

1. Get file ID via `files().list` (search by name), download via `files().get_media` (PDFs OK).
2. pymupdf `get_text()`: if page 1 head is empty → scanned image, NO text layer (normal for registered deed scans).
3. OCR scanned deeds with tesseract: render at `dpi=200, colorspace=fitz.csGRAY`, `tesseract <png> stdout --psm 6`. OCR page 1 (parties), page 2 (stamp/challan), LAST page (identifiers/signature block).
4. Key-term grep on extracted text: grantor ("DRA REALTY PRIVATE LIMITED"), grantee ("BHARAT BABURAO HAWALDAR"), "SPECIAL POWER OF ATTORNEY", "IN FAVOUR OF", purpose verbs ("admit and present for registration", "Joint Development Agreements"), registration no ("GNR-4-00675-2025-26"), "Identifier".

## Reading a deed correctly

- **Registration/end pages show WHO PRESENTED the deed** (SPA-holder vs Director). Example: the Ranka Amber JDA (Reg 2227/2025-26) registration page shows "presented by Director Nishant Ranka" — Bharat's name appears in the JDA text but he did NOT act as presenter. Read the end pages before claiming someone acted under a POA.
- **Direction matters.** "Ranka Amber GPA for JDA" was landowners (Farida & Raghu Iyer) → DRA Realty irrevocable GPA — the OPPOSITE direction from a DRA → employee SPA. Always state grantor→grantee.
- **Entity classes differ.** SPAs exist from DRA Realty Pvt Ltd, from individuals (NDR personally — e.g. Ashokji Mortgage Deed SPA), and from land-partner entities (DRA Thindlu Land Partners) — report each class separately, don't blur them.
- Registered deed scans carry **registration receipt pages** (challan no, doc no, date, identifiers) — those are the proof it was registered, cite them.

## Deliverable shape

Per found deed: registration no + date, grantor→grantee, purpose scope (properties/region), Drive link. For "give me the link": `drive.files().get(fileId=..., fields='webViewLink,parents')` + parent folder name; NDR also accepts the PDF as a MEDIA attachment.