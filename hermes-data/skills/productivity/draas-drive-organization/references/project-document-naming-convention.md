# DRAAS Project Document Naming Convention (Google Drive)

## The convention

```
YYYYMMDD_ProjectName_Description.ext
```

- **YYYYMMDD** — date the document was created/issued (not uploaded)
- **ProjectName** — project name in CamelCase: `RankaAmber`, `CloverGreens`, `Oasis`
- **Description** — what the document is, underscore-separated: `BMTF_Notice_Endorsement`, `ICICI_APF_Approval_KA-BAN-26-61572`, `GPA_for_JDA_ContactDetails_Updated`
- No spaces anywhere — underscores as word separators

## Examples from live Drive files

```
20260925_RankaAmber_ICICI_APF_Approval_KA-BAN-26-61572.pdf
20260918_RankaAmber_BMTF_Notice_Endorsement.pdf
20260903_RankaAmber_BMTF_Police_Notice_Original_Scan.pdf
20260903_RankaAmber_BMTF_Police_Notice_English_Translation.pdf
20260903_RankaAmber_BMTF_Police_Notice.pdf
20260624_RankaAmber_SupplementarySharingAgreement_Signed_Copy_For_DRA.pdf
20260918_RankaAmber_GPA_for_JDA_ContactDetails_Updated.pdf
20260824_Ranka_Amber_DPR.docx                       ← minor variant with underscore in project name, acceptable
```

Note: `RankaAmber` (no space) is preferred over `Ranka_Amber` (with underscore), but both are seen in practice. Pick one per project and stay consistent within the folder.

## Exceptions / non-applicable cases

- **Personal/financial docs (Form 16s, salary slips, tax records):** use `personal-document-organization` skill instead (local filesystem convention)
- **School reports / certificates:** per-child folder on Drive, child-first naming (see `personal-document-organization` skill's school docs section)
- **Marketing collateral / renders:** file into the project's marketing folder, rename to human-readable names (brochure name, version number)
- **Invitations / personal events:** `YYYYMMDD_Event_Name_Venue.jpg` — see `references/personal-invites-drive-calendar.md`

## How to determine the correct name when filing

1. **Date:** extract from the document itself (letterhead, signature, email header). Use creation date as last resort.
2. **Project:** resolve via `entity_resolver` if the project name isn't obvious from the document content. Use the canonical project name as it appears in other Drive folder names.
3. **Description:** concise, specific, underscore-separated. For legal documents, mirror existing file descriptions in the same folder (e.g. if existing files use `BMTF_Police_Notice`, use `BMTF_Notice_Endorsement` for the endorsed reply).

## Filing workflow for a user-uploaded document

1. Open the PDF — extract text (pdftotext for text PDFs, pymupdf → pdftoppm → vision_analyze for scanned PDFs)
2. Identify: project, document type, date, sender/author (e.g. VK Das draft, BBMP notice, bank approval)
3. Search Drive for existing files with the same project + keyword to confirm the naming pattern and target folder
4. Rename per convention
5. Upload to the project's appropriate subfolder on Drive (e.g. `Ranka Amber → Ranka Amber Legal Notices`, `Ranka Amber → Ranka Amber Banking and Finance`)
6. Verify the file landed in the correct folder